#!/usr/bin/python3
from __future__ import print_function

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import sys
import scipy
from tqdm import tqdm

import django
from django.utils import timezone
from django.db.models import Count


django.setup()

from papers.models import Article, Feature
import papers.utils as utils

def get_articles_without_features():
    articles = Article.objects.annotate(num_children=Count('feature')).filter(num_children=0)
    data = []
    for art in articles:
        data.append( (art.title, art.authors, art.abstract, art.keywords) )
    return articles, data

def get_features(data):
    features = scipy.sparse.csr_matrix( utils.compute_features( data ) )
    return features

def add_features_to_db(articles, features, stride = 200):
    for k in tqdm(xrange(len(articles)/stride+1)):
        start = k*stride
        end   = min((k+1)*stride,features.shape[0])
        A = scipy.sparse.coo_matrix(features[start:end])
        Feature.objects.bulk_create( [ Feature( article=articles[int(i+k*stride)], index=int(j), value=float(v)) for i,j,v in zip(A.row, A.col, A.data) ] )

if __name__ == "__main__":
    # Feature.objects.all().delete()

    print("Finding articles without features...")
    articles, data = get_articles_without_features()

    if not len(data):
        sys.exit()

    print("Computing features for %i articles..."%(len(data)))
    features = get_features(data)

    print("Adding %i feature vectors to db... "%(features.shape[0]))
    add_features_to_db(articles, features)
