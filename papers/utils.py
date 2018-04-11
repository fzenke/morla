#!/usr/bin/python
from scipy import sparse
from sklearn.feature_extraction.text import HashingVectorizer
import numpy as np
import re
from tqdm import tqdm

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import django
from django.utils import timezone
from django.utils.encoding import smart_text
from django.db.models import Q

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
# from pylatexenc.latex2text import latex2text 
from datetime import datetime


django.setup()

from papers.models import Article, Profile, Feature, Recommendation, Similarity
from django.contrib.auth.models import User


feature_dims = { 'title' : 2**20,  'authors' : 2**16,  'abstract' : 2**20, 'keywords' : 2**16 }
feature_weights = { 'title' : 1.0,  'authors' : 1.0,  'abstract' : 1.0, 'keywords' : 1.0 }



def get_recommended_articles(request):
    articles = []
    if request.user.is_authenticated:
        profile,_ = Profile.objects.get_or_create(user=request.user, defaults={'last_prediction_run': timezone.now(), 'last_traindata_update': timezone.now()})
        articles = profile.suggested.all().order_by('-pubdate')
    else: # Get suggested articles from all users
        articles = Article.objects.filter(suggested__isnull=False).distinct().order_by('-pubdate')
    return articles

def get_similar_articles(article, limit=13):
    # similarities = Similarity.objects.filter( a=article ).order_by('-value')[:limit]
    similarities = Similarity.objects.filter( Q(a=article) | Q(b=article) ).order_by('-value')[:limit]
    articles = []
    for s in similarities:
        if s.a==article:
            articles.append(s.b)
        else:
            articles.append(s.a)
    return articles

def set_label(request, article_id, label=0):
    """ Adds article to training set of the authenticated user with given label 
    
    args:
        request the request object
        article_id the article id
        label the label which is either 1 for ham, -1 for spam or 0 which removes the label
    """
    if not request.user.is_authenticated: return False

    profile,_ = Profile.objects.get_or_create(user=request.user, defaults={'last_prediction_run': timezone.now(), 'last_traindata_update': timezone.now()})
    article = Article.objects.get(id=article_id)
    label = int(label)

    if label > 0:
        profile.ham.add(article)
        profile.spam.remove(article)
    elif label < 0:
        profile.spam.add(article)
        profile.ham.remove(article)
    else:
        profile.ham.remove(article)
        profile.spam.remove(article)

    # Store time when we last updated the profile
    profile.last_traindata_update = timezone.now()
    profile.save()

    return True

def toggle_star(request, article_id):
    """ Stars article or removes star if already starred
    
    args:
        request the request object
        article_id the article id

    returns True if successful otherwise False

    """
    if not request.user.is_authenticated: return 0

    profile,_ = Profile.objects.get_or_create(user=request.user, defaults={'last_prediction_run': timezone.now(), 'last_traindata_update': timezone.now()})
    article = Article.objects.get(id=int(article_id))

    if profile.starred.filter(id=article_id).exists():
        profile.starred.remove(article)
        return 0
    else:
        profile.starred.add(article)

    return 1

# Prepare re_pattern to filter Unicode which would take more than 3bytes (to avoid MySQL trouble)
re_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
def filter_using_re(unicode_string):
    return re_pattern.sub(u'\uFFFD', unicode_string)

def prepare_string(x, max_length=None):
    """ Converts a string from LaTeX escapes to UTF8 and truncates it to max_length """
    # data = latex2text(x, tolerant_parsing=True)
    data = x
    if max_length is not None:
        data = (data[:max_length-5] + '[...]') if len(data) > max_length else data
    return smart_text(filter_using_re(data))

def key2str(key, dic, max_length=None):
    """ Gets entry from dict and returns an empty string if the key does not exist. """
    if key in dic.keys():
        return prepare_string(dic[key], max_length=max_length)
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

def import_bibtex(bibtex_str, nb_max=None, update=True):
    """ Reads a bibtex string and returns a list of Article instances """ 

    parser = BibTexParser(ignore_nonstandard_types=False, homogenize_fields=False, common_strings=True)
    parser.customization = convert_to_unicode
    bib_database = bibtexparser.loads(bibtex_str, parser)
 
    logger.info("Entries read from BibTeX data %i"%len(bib_database.entries))

    # packaging into django objects
    data = []
    for e in bib_database.entries:
        title = key2str('title',e, 250)
        authors  = key2str('author',e,500)
        journal  = key2str('journal',e,250)
        abstract = key2str('abstract',e)
        if not key2int('year',e) or not abstract or not title: continue 
        pubdate = datetime(key2int('year',e),1,1)
        keywords = key2str('keyword',e,250)
        args = dict(title=title, 
                authors=authors, 
                pubdate=pubdate,
                journal=journal,
                abstract=abstract,
                keywords=keywords,
                url=key2str('link',e),
                doi=key2str('doi',e),
                pmid=key2int('pmid',e),
                )
        if update:
            art, created = add_or_update_article(**args)
        else:
            art, created = get_or_create(**args)

        art.save()
        data.append(art)

        if nb_max is not None:
            if len(data)>=nb_max:
                break

    logger.info("%i entries processed"%len(data))
    return data

def compute_features( data ):
    """ Converts a list of tuples with title, authors, abstract, keywords to sparse tokenized feature vectors. """
    titles, authors, abstracts, keywords = zip(*data)

    shared_params = dict(stop_words='english', strip_accents=None, non_negative=True )
    title_vectorizer    = HashingVectorizer( n_features=feature_dims['title'], **shared_params )
    authors_vectorizer  = HashingVectorizer( n_features=feature_dims['authors'], **shared_params )
    # journal_vectorizer  = HashingVectorizer( n_features=feature_dims['journal'], **shared_params )
    abstract_vectorizer = HashingVectorizer( n_features=feature_dims['abstract'], **shared_params )
    keywords_vectorizer = HashingVectorizer( n_features=feature_dims['keywords'], **shared_params )

    title_vecs = title_vectorizer.transform(titles)
    authors_vecs = authors_vectorizer.transform(authors)
    # journal_vecs = journal_vectorizer.transform(journals)
    abstract_vecs = abstract_vectorizer.transform(abstracts)
    keyword_vecs = keywords_vectorizer.transform(keywords)

    # Compute feature weights
    title_vecs    = title_vecs.multiply(feature_weights['title'])
    authors_vecs  = authors_vecs.multiply(feature_weights['authors'])
    abstract_vecs = abstract_vecs.multiply(feature_weights['abstract'])
    keyword_vecs = keyword_vecs.multiply(feature_weights['keywords'])

    feature_vectors = sparse.hstack((title_vecs, authors_vecs, abstract_vecs, keyword_vecs))
    return feature_vectors

def get_feature_vector( article ):
    fts = Feature.objects.filter( article=article )
    index = fts.values_list('index', flat=True)
    val = fts.values_list('value', flat=True)
    return index, val

def get_feature_vector_size():
    feature_vector_size = 0
    for itm in feature_dims.values():
        feature_vector_size += itm
    return feature_vector_size


def get_features_from_db( articles ):
    data = []
    row = []
    col = []
    for i,ai in enumerate(articles):
        c,v = get_feature_vector( ai )
        r = np.ones(len(c))*i
        data.extend(v)
        row.extend(r)
        col.extend(c)

    A = sparse.coo_matrix( (data, (row, col)), shape=(len(articles),get_feature_vector_size()))
    return A


def add_to_training_set( profile, articles, label ):
    """ Takes a user and a list of articles and adds them as training data with the given label """
    if label>0:
        profile.ham.add(*articles)
    elif label<0:
        profile.spam.add(*articles)


def add_or_update_article(title, authors, pubdate, journal, abstract, url=None, doi=None, keywords=None, pmid=None ):
    art, created = Article.objects.get_or_create(
            title=title, 
            authors=authors,
            defaults={ 'pubdate' : pubdate, 'date_added' : timezone.now() }
            )

    art.journal=journal
    art.pubdate=pubdate
    art.abstract=abstract
    art.url=url
    art.doi=doi
    if keywords is not None: art.keywords=keywords
    if pmid is not None: art.pmid=pmid
    art.date_added = timezone.now()
    art.save()

    Feature.objects.filter( article=art ).delete()
    return art, created


def get_or_create(title, authors, pubdate, journal, abstract, url=None, doi=None, keywords=None, pmid=None ):
    art, created = Article.objects.get_or_create(
            title=title, 
            authors=authors,
            defaults={ 'pubdate' : pubdate, 'date_added' : timezone.now() }
            )

    if created:
        art.journal=journal
        art.abstract=abstract
        art.url=url
        art.doi=doi
        if keywords is not None: art.keywords=keywords
        if pmid is not None: art.pmid=pmid
        art.save()

    return art, created

def get_training_set( profile, padrandom=True ):
    articles = list( profile.ham.all() )
    labels = [ 1 for i in range(len(articles)) ]
    spam = profile.spam.all()
    articles.extend( spam )
    labels.extend( [ -1 for i in range(len(spam)) ] ) 

    nb_pad = profile.ham.all().count() - profile.spam.all().count()
    if padrandom and nb_pad>0: 
        logger.debug("Using %i random patterns to augment spam set"%nb_pad)
        pad = Article.objects.exclude(ham=profile).order_by('?')[:nb_pad] 
        articles.extend( pad )
        labels.extend( [ -1 for i in range(len(pad)) ] ) 

    data = get_features_from_db( articles )
    return data, np.array(labels)



if __name__ == "__main__":
    profile,_ = Profile.objects.get_or_create(user=User.objects.all()[0])
    data, labels = get_training_set( profile )
    print(data)
    print(labels)

