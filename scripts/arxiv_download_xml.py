#!/usr/bin/env python3

# Based on code by https://github.com/dfm
# from https://github.com/dfm/arxiv-analysis/blob/master/arxiv/scrape.py

from __future__ import print_function

__all__ = [u"get"]

import os
import re
import time
import requests

sleep_time = 20
resume_re = re.compile(r".*<resumptionToken.*?>(.*?)</resumptionToken>.*")
url = "http://export.arxiv.org/oai2"


def get(basepath=u".", max_tries=10):
    """
    Get all the listings from the ArXiv.
    """
    req = {u"verb": "ListRecords",
           u"metadataPrefix": u"arXivRaw",
           u"from": "2016-01-01",
           u"until": "2018-01-31"}

    failures = 0
    count = 0
    while True:
        # Send the request.
        r = requests.post(url, data=req)

        # Handle the response.
        code = r.status_code

        if code == 503:
            # Asked to retry
            to = int(r.headers["retry-after"])
            print(u"Got 503. Retrying after {0:d} seconds.".format(to))

            time.sleep(to)
            failures += 1
            if failures >= max_tries:
                print(u"Failed too many times...")
                break

        elif code == 200:
            failures = 0

            # Write to file.
            content = r.text
            count += 1
            fn = os.path.join(basepath, u"raw-{0:08d}.xml".format(count))
            print(u"Writing to: {0}".format(fn))
            with open(fn, u"w") as f:
                f.write(content)

            # Look for a resumption token.
            token = resume_re.search(content)
            if token is None:
                break
            token = token.groups()[0]

            # If there isn't one, we're all done.
            if token == "":
                print(u"All done.")
                break

            print(u"Resumption token: {0}.".format(token))

            # If there is a resumption token, rebuild the request.
            req = {u"verb": u"ListRecords",
                   u"resumptionToken": token}

            # Pause so as not to get banned.
            print(u"Sleeping for {0:d} seconds so as not to get banned."
                    .format(sleep_time))
            time.sleep(sleep_time)

        else:
            # Wha happen'?
            r.raise_for_status()


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        bp = u"."
    else:
        bp = sys.argv[1]

    get(basepath=bp)



