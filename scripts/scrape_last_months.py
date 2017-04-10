#!/usr/bin/python
from __future__ import print_function

import datetime
from scrape_bioarxiv import *

if __name__ == "__main__":
    start_date = datetime.date(2016, 1, 11)
    scrape_articles(start_date=start_date)
