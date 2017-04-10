#!/usr/bin/env python

# Based on code by https://github.com/dfm
# from https://github.com/dfm/arxiv-analysis/blob/master/arxiv/scrape.py

from __future__ import print_function

import os,sys,inspect
import re
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import requests
import logging
import datetime
import time
from tqdm import tqdm

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(10)

from bs4 import BeautifulSoup as bs

import django
from django.utils import timezone
from django.utils.encoding import smart_text


django.setup()

from papers.models import Article, Profile
from django.contrib.auth.models import User

import papers.utils as utils


resume_re = re.compile(r".*<resumptionToken.*?>(.*?)</resumptionToken>.*")
export_url = "http://export.arxiv.org/oai2"
harvest_sets = ['q-bio','cs', 'stat']

base_url = "https://arxiv.org/abs"


def conv_str(x, max_length=None):
    return utils.prepare_string(x.text.strip(), max_length)

def process_xml(data, journal_name):
    """ Process raw arxive xml data and insert them into the database.

    args:
        data the xml data
    returns: 
        list of articles added or updated
    """

    xml = bs(data, 'lxml')
    raw_articles = xml.find_all('record')
    for entry in tqdm(raw_articles):
        arxiv_id = entry.find('id').text
        title    = conv_str(entry.find('title'),250)
        authors  = conv_str(entry.find('authors'),500)
        abstract = conv_str(entry.find('abstract'))
        date_str = conv_str(entry.find('date'))
        pubdate = datetime.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT") # presumably get the date of the first version
        # categories = xml.find('categories') # not used

        doi = entry.find('doi')
        if doi: 
            doi = doi.text.strip()
        else:
            doi = ""
        url = "%s/%s"%(base_url,arxiv_id)

        # create database object
        art, created = utils.add_or_update_article(
                title=title, 
                authors=authors,
                pubdate=pubdate,
                journal=journal_name,
                abstract=abstract,
                url=url,
                doi=doi,
                )

        if created:
            logger.debug("Added article %i: %s"%(art.id,title))
        else:
            logger.debug("Updated article %i: %s"%(art.id,title))



def scrape_articles(start_date=None, end_date=None, harvest_set=None, max_tries=10, timedelta=1):
    """
    Get raw data from the ArXiv.
    """

    sleep_time = 20

    if end_date is None:
        end_date = datetime.date.today()

    if start_date is None:
        start_date = datetime.date.today() - datetime.timedelta(timedelta)

    # Prepare request to OAI API
    req = {"verb": "ListRecords",
           "metadataPrefix": "arXivRaw",
           "from": start_date,
           "until": end_date}

    journal_name = 'arXiv' 
    if harvest_set is not None:
        req["set"] = harvest_set
        journal_name = 'arXiv ' + harvest_set

    failures = 0
    count = 0
    while True:
        # Send request and handle response
        r = requests.post(export_url, data=req)
        code = r.status_code

        logger.debug("Sleeping for %i seconds to not hammer the server."%sleep_time)
        time.sleep(sleep_time)

        if code == 503: # retry later
            sleep_time = int(r.headers["retry-after"])
            logger.warning("Error 503. Retrying...")
            failures += 1
            if failures >= max_tries:
                logger.error("Failed too many times...")
                break

        elif code == 200: # OK
            failures = 0
            data = r.text
            count += 1
            # process content
            process_xml(data, journal_name)

            # Look for a resumption token
            token = resume_re.search(data)
            if token is None:
                break
            token = token.groups()[0]

            # Done when there is none
            if token == "":
                logger.info("Done.")
                break

            logger.debug("Resumption token: %s".format(token))

            # If there is a resumption token, rebuild the request.
            req = {"verb": "ListRecords",
                   "resumptionToken": token}


        else:
            r.raise_for_status()


if __name__ == "__main__":

    for s in harvest_sets:
        logger.info("Importing %s"%s)
        scrape_articles(harvest_set=s)

