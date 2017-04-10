#!/bin/sh

. ./setenv.sh

python scrape_bioarxiv.py
python scrape_arxiv.py

python compute_feature_vectors.py
python compute_recommendations.py
python compute_gramian.py
