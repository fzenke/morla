#!/usr/bin/python3

# Code based on work by http://predictablynoisy.com
# from http://predictablynoisy.com/scrape-biorxiv.html

from __future__ import print_function

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import requests
import pandas as pd
import seaborn as sns
import numpy as np
from bs4 import BeautifulSoup as bs
import matplotlib.pyplot as plt
from tqdm import tqdm
import datetime
import time
import datetime

import django
from django.utils import timezone
from django.utils.encoding import smart_text


django.setup()

from papers.models import Article, Profile
from django.contrib.auth.models import User

import papers.utils as utils

# Define the URL parameters
n_results = 400
search_term = ""
url_base = "http://biorxiv.org"
url_search_base = url_base + "/search/{}".format(search_term)
url_params = "%20limit_from%3A{0}-{1}-{2}%20limit_to%3A{0}-{1}-{3}%20numresults%3A{3}%20format_result%3Aascending format_result%3Astandard"
url_template = url_search_base + url_params


def scrape_articles(start_date=None, end_date=None):
    if end_date is None:
        end_date = datetime.date.today()

    if start_date is None:
        start_date = datetime.date.today() - datetime.timedelta(1)

    # Now we'll do the scraping...
    all_articles = []
    current_date = start_date
    while current_date<end_date:
        yr = current_date.year
        mn = current_date.month
        dy = current_date.day
        current_date +=  datetime.timedelta(1) 

        print("Processing %i-%i-%i"%(yr,mn,dy))
        # Populate the fields with our current query and post it
        this_url = url_template.format(yr, mn, dy, dy+1, n_results) 
        resp = requests.post(this_url)
        html = bs(resp.text, 'lxml')
        
        # Collect the articles in the result in a list
        raw_articles = html.find_all('li', attrs={'class': 'search-result'})
        for entry in raw_articles:
            time.sleep(0.1)
            e = {}
            # Pull the title, if it's empty then skip it
            title_link = entry.find('a', attrs={'class': 'highwire-cite-linked-title'})
            if title_link is None:
                continue

            # Extract title
            title = title_link.text.strip()
            # Extract url
            url = url_base + title_link.get('href')

            # Extract date from url
            str = title_link.get('href')
            sp = str.split('/')
            date = datetime.date(int(sp[3]), int(sp[4]), int(sp[5]))

            # Collect author information
            authors_raw = entry.find_all('span', attrs={'class': 'highwire-citation-author'})
            authors = ""
            for i, author in enumerate(authors_raw):
                authors += author.text 
                if i < len(authors_raw)-1:
                    authors += ", "

            doi = entry.find('span', attrs={'class': 'highwire-cite-metadata-doi'})
            doi = doi.text.strip()
            doi = doi.replace("doi: ", "", 1)
            doi = doi.replace("https://doi.org/", "", 1)

            # Get the abstract
            detail_resp = requests.post(url)
            detail_html = bs(detail_resp.text, 'lxml')
            abstract_raw = detail_html.find('div', attrs={'class': 'section abstract'})
            #with open('dump.txt','w') as f:
            #    f.write(detail_resp.text.encode('utf8'))
            if abstract_raw is None:
                continue
            abstract = abstract_raw.text.strip().replace("Abstract","",1)

            
            # Set this statically
            journal = 'bioRxiv'

            # append categories to journal name
            categories_raw = detail_html.find_all('span', attrs={'class': 'highwire-article-collection-term'})
            for i, cat in enumerate(categories_raw):
                journal += " "
                journal += cat.text

            # create database object
            art, created = utils.add_or_update_article(
                    title=utils.prepare_string(title,250), 
                    authors=utils.prepare_string(authors,500),
                    pubdate=date,
                    journal=utils.prepare_string(journal,250),
                    abstract=utils.prepare_string(abstract),
                    url=url,
                    doi=doi,
                    )

            if created:
                print("Added article %i: %s"%(art.id,title))
            else:
                print("Updated article %i: %s"%(art.id,title))

            all_articles.append(art)



    print("Finished processing %i articles"%(len(all_articles)))


if __name__ == "__main__":
    scrape_articles()
