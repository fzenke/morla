#!/usr/bin/python
from __future__ import print_function

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import numpy as np
import scipy
from scipy import sparse
from tqdm import tqdm


import matplotlib.pyplot as plt

from sklearn.svm import LinearSVC
import gzip
import cPickle as pickle
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn import metrics
from time import time

import django
from django.utils import timezone
from django.db.models import Max

django.setup()

from papers.models import Article, Feature, Profile, Recommendation, Similarity

import papers.utils as utils
from compute_feature_vectors import *



def compute_gramian(start_block=0, maxblock=None, cutoff=0.25, block_size=1000):
    """ Computes the gramian matrix from feature vectores stored in the databse

    The function computes the sparse Gramian from feature vectors stored in the database. 
    To avoid loading the entire Gramian in memory, it is build from block matrices which are
    computed individually, sparsified (with a cutoff value) and then combined to one large 
    sparse matrix.

    params:
    block_size The block size for the sub matrices
    start_block Assumes that the Gramian until start_block is already computed and only computes the rest
    maxblock Limits the block number to a maximum (for testing). When set to None the entire matrix is computed
    cutoff The cutoff value for the scalar product.

    returns:
    Sparse matrix Gramian in coo format
    """

    articles = Article.objects.all()
    nb_articles = articles.count()
    bs = block_size
    if maxblock is None:
        lb = nb_articles/bs+1
    else:
        lb = maxblock

    print("Computing Gramian for %i articles in blocks of %i..."%(nb_articles, block_size))
    blocks = [ [None for i in xrange(lb)] for j in xrange(lb) ]
    for i in tqdm(xrange(lb)):
        lower_row = int(i*bs)
        upper_row = int((i+1)*bs)
        if i==lb-1: upper_row=nb_articles
        for j in xrange(i,lb):
            if j<start_block: continue
            lower_col = int(j*bs)
            upper_col = int((j+1)*bs)
            if j==lb-1: upper_col=nb_articles
            tmp = utils.get_features_from_db(Article.objects.all()[lower_row:upper_row])
            A = scipy.sparse.csr_matrix(tmp)
            tmp = utils.get_features_from_db(Article.objects.all()[lower_col:upper_col])
            B = scipy.sparse.csr_matrix(tmp)
            B = scipy.sparse.csc_matrix(tmp.transpose())
            C = A.dot(B)
            if i==j:
                C = sparse.tril(C,-1)
            C = C.multiply(C >= cutoff )
            blocks[i][j] = C

    print("Saving to db...")
    data = sparse.bmat(blocks,'coo')
    print("sparseness=%f"%(1.0*data.nnz/np.prod(data.shape)))
    add_similarities_to_db(articles[:nb_articles], data)



def add_similarities_to_db(articles, C, commit_count=5000):
    off = C.shape[0]-C.shape[1]
    transaction = []
    for i in tqdm(xrange(len(articles))):
        a = articles[i]

        # All all elements in row of similarity matrix
        row = C.getrow(i)
        _,idx,vals = sparse.find(row)
        transaction.extend( [ Similarity( a=a, b=articles[int(k+off)], value=v) for k,v in zip(idx, vals) ] )

        if len(transaction)>commit_count:
            Similarity.objects.bulk_create( transaction )
            transaction = []

    Similarity.objects.bulk_create( transaction )


def compute_features():
    articles, data = get_articles_without_features()

    if len(data):
        print("Computing features for %i articles..."%(len(data)))
        features = get_features(data)

        print("Adding %i feature vectors to db... "%(features.shape[0]))
        add_features_to_db(articles, features)


def update_gramian(block_size=1000):
    # Find first article without similarities 
    start_block = 0
    if Similarity.objects.all().count():
        qres = Similarity.objects.all().aggregate(Max('a'))
        start_block = int(qres['a__max']/block_size)
        print("Resuming at article_id=%i"%qres['a__max'])
    # Remove any junk above the blocksize limit
    Similarity.objects.filter(a__gt=start_block*block_size).delete()
    Similarity.objects.filter(b__gt=start_block*block_size).delete()
    # Compute the remaining blocks and add them to DB
    compute_gramian(start_block=start_block, block_size=block_size)


def rebuild_full_gramian():
    Similarity.objects.all().delete()
    compute_gramian()


if __name__ == "__main__":
    print("Checking for missing feature vectors...")
    compute_features()

    print("Updating full Gramian...")
    # Similarity.objects.all().delete()
    update_gramian()

