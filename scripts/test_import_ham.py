#!/usr/bin/python
from __future__ import print_function

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import bibtexparser
import re
from datetime import datetime

import django
from django.utils import timezone
from django.utils.encoding import smart_text


django.setup()

from papers.models import Article, Profile
from django.contrib.auth.models import User

import papers.utils as utils

def remove_junk(x):
    return re.sub('[{}\\\]', '', x)

def key2str(key, dic):
    """ Gets entry from dict and returns an empty string if the key does not exist. """
    if key in dic.keys():
        return smart_text(remove_junk(dic[key]))
    else:
        return ''

def key2int(key, dic):
    """ Gets integer entry from dict and returns None if the key does not exist or if there is a ValueError. """
    value=None
    if key in dic.keys():
        try:
            value=int(dic[key])
        except ValueError:
            value=None
    return value

def import_bibtex(filename='library.bib'):
    """ Reads a bibtex file and returns a list of Article instances """ 
    with open(filename) as bibtex_file:
        bibtex_str = bibtex_file.read()

    bib_database = bibtexparser.loads(bibtex_str)
    print("Entries read from BibTeX file %i"%len(bib_database.entries))

    # packaging into django objects
    data = []
    for e in bib_database.entries:
        title = key2str('title',e)
        abstract = key2str('abstract',e)
        if not key2int('year',e) or not abstract or not title: continue 
        pubdate = datetime(key2int('year',e),1,1)
        keywords = key2str('keyword',e)
        # truncate keywords
        keywords = (keywords[:250]) if len(keywords) > 250 else keywords

        art, created = utils.add_or_update_article(title=title, 
                authors=key2str('author',e), 
                pubdate=pubdate,
                journal=key2str('journal',e),
                abstract=abstract,
                keywords=keywords,
                url=key2str('link',e),
                doi=key2str('doi',e),
                pmid=key2int('pmid',e),
                )
        art.save()
        data.append(art)

    print("Entries added or updated in database %i"%len(data))
    return data


if __name__ == "__main__":
    # articles = import_bibtex('../goldret/ham.bib')
    # utils.add_to_training_set( User.objects.all()[0], articles, 1 )
    articles = import_bibtex('../../data/ham.bib')
    profile,_ = Profile.objects.get_or_create(user=User.objects.get(username='zenke'))
    utils.add_to_training_set( profile, articles, 1 )

