#!/bin/sh

. ./setenv.sh

python3 scrape_bioarxiv.py
python3 scrape_arxiv.py

python3 compute_feature_vectors.py
python3 compute_recommendations.py
python3 compute_gramian.py
