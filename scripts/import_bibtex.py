#!/usr/bin/python
from __future__ import print_function

import django
from django.utils import timezone


django.setup()

from papers.models import Article, Profile
from django.contrib.auth.models import User

import papers.utils as utils

if __name__ == "__main__":
    filename = '../../data/all.bib'
    with open(filename) as bibtex_file:
        bibtex_str = bibtex_file.read()
    articles = utils.import_bibtex(bibtex_str)

