#!/usr/bin/python
from __future__ import print_function

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import numpy as np
import papers.utils as utils

from sklearn.svm import LinearSVC
import gzip
import cPickle as pickle
import datetime

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import django
from django.utils import timezone
from django.db.models import Max
from django.db.models import F
from django.db.models import Q

django.setup()

from papers.models import Article, Feature, Profile, Recommendation

from compute_feature_vectors import *

min_number_of_ham = 4
consider_inactive_after_days = 60


def compute_recommendations(profile, articles, data, show_training_data=True, max_suggestions=500):
    logger.info("Loading training data for profile %s..."%profile)
    X_train, y_train = utils.get_training_set( profile )
    logger.debug("%i samples in training set (%i positive)"%(len(y_train), (y_train>0).sum()))

    # See if conditions for fit are met
    if X_train.shape[0] > min_number_of_ham:
        logger.debug("Fitting SVM...")
        svm = LinearSVC()
        svm.fit(X_train, y_train)

        logger.debug("Validating...")
        predictions = svm.predict(X_train)
        logger.debug("%f%% train accuracy"%(100*(predictions==y_train).mean()))

        logger.debug("Predicting...") 
        predictions = svm.predict(data)
        logger.debug("%f%% relevant"%(100*(predictions==1).mean()))

        logger.debug("Saving recommendations...")
        recommended_articles = []
        for a,p in zip(articles, predictions):
            if p>0:
                if show_training_data: 
                    recommended_articles.append(a)
                elif not profile.ham.filter(id=a.id).exists(): 
                    recommended_articles.append(a)

            if len(recommended_articles)>=max_suggestions:
                break

        Recommendation.objects.filter( profile=profile ).delete()
        Recommendation.objects.bulk_create( [ Recommendation( profile=profile, article=a, date_added=timezone.now() ) for a in recommended_articles ] )
        logger.info("Saved %i suggestions"%(len(recommended_articles)))

    # Save last prediction time to profile
    profile.last_prediction_run = timezone.now()
    profile.save()



if __name__ == "__main__":
    logger.debug("Loading user profiles...")
    # get users which need updating
    qres = Article.objects.all().aggregate(Max('date_added'))
    min_last_time_active = timezone.now() - datetime.timedelta(consider_inactive_after_days)
    profiles = Profile.objects.filter( Q(last_time_active__lte=min_last_time_active) | Q(last_prediction_run__lte=F('last_traindata_update')) | Q(last_prediction_run__lte=qres['date_added__max']) )
    # profiles = Profile.objects.all()
    
    if profiles:
        logger.info("Loading articles...")
        from_date = datetime.date.today() - datetime.timedelta(356)
        articles = Article.objects.filter(pubdate__gte=from_date).order_by('-pubdate')

        logger.debug("Loading data ...")
        data = utils.get_features_from_db(articles)
      
        for profile in profiles:
            compute_recommendations(profile, articles, data)
    else:
        logger.debug("Nothing to do. Exiting...")
