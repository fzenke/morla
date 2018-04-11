from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.http import JsonResponse, HttpResponseRedirect

from . import utils 

from papers.models import Article, Profile, Feature, Recommendation, Similarity

from .forms import UploadFileForm

# from django.contrib.auth.models import User

def index(request):
    return suggested(request)

def detail(request, article_id):
    template = loader.get_template('papers/details.html')
    article = Article.objects.get(id=article_id)

    in_training_set = ""
    if request.user.is_authenticated:
        profile,_ = Profile.objects.get_or_create(user=request.user)
        if profile.ham.filter(id=article_id).exists():
            in_training_set = "ham"
        elif profile.spam.filter(id=article_id).exists():
            in_training_set = "spam"

    context = {
        'article': article,
        'in_training_set': in_training_set,
        'similar_articles': utils.get_similar_articles(article)
    }
    return HttpResponse(template.render(context, request))


def paginated_list(request, all_articles, title="", elements_per_page=50):
    paginator = Paginator(all_articles, elements_per_page) 
    page = request.GET.get('page')
    try:
        articles_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        articles_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        articles_list = paginator.page(paginator.num_pages)

    template = loader.get_template('papers/paginated_list.html')
    context = {
        'title': title,
        'articles_list': articles_list,
    }
    return HttpResponse(template.render(context, request))

def list(request, all_articles, title="", elements_per_page=50):
    if ( len(all_articles) > elements_per_page ):
        return paginated_list(request=request, all_articles=all_articles, title=title, elements_per_page=elements_per_page)
    else:
        template = loader.get_template('papers/list.html')
        context = {
            'title': title,
            'articles_list': all_articles,
        }
        return HttpResponse(template.render(context, request))

def suggested(request):
    all_articles = utils.get_recommended_articles(request)
    return list(request, all_articles, title="Suggested")

def all(request):
    return list(request, Article.objects.order_by('-date_added'), title="All papers")

def recent(request):
    return list(request, Article.objects.order_by('-pubdate'), title="Recent")

def random(request):
    return list(request, Article.objects.order_by('?')[:30], title="Random")

@login_required
def starred(request):
    if request.user.is_authenticated:
        profile,_ = Profile.objects.get_or_create(user=request.user)
        starred_articles = profile.starred.all().order_by('-date_added')
    return list(request, starred_articles, title="Starred")

@login_required
def ham(request):
    if request.user.is_authenticated:
        profile,_ = Profile.objects.get_or_create(user=request.user)
        articles = profile.ham.all().order_by('-date_added')
    else:
        articles = []
    return list(request, articles, title="Positive training examples (ham)")

@login_required
def upload_ham_bib_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid() and request.user.is_authenticated:
            articles = utils.import_bibtex(request.FILES['file'].read(), nb_max=200, update=True) # FIXME should be set to False at some point
            profile,_ = Profile.objects.get_or_create(user=request.user)
            utils.add_to_training_set( profile, articles, +1 )

            return HttpResponseRedirect('/papers/ham')
    else:
        form = UploadFileForm()

    return render(request, 'papers/upload.html', {'form': form})

@login_required
def spam(request):
    if request.user.is_authenticated:
        profile,_ = Profile.objects.get_or_create(user=request.user)
        articles = profile.spam.all().order_by('-date_added')
    else:
        articles = []
    return list(request, articles, title="Negative training examples (spam)")


@login_required
def ajax_set_label(request):

    if request.method == 'GET':
        article_id = request.GET['article_id']
        label = request.GET['label']

    if article_id:
        err = utils.set_label(request,article_id,label)

    response_data = {}
    response_data['article_id'] = article_id
    response_data['result'] = label
    return JsonResponse(response_data)


@login_required
def ajax_toggle_star(request):
    ret = 0
    if request.method == 'GET':
        article_id = request.GET['article_id']
        if article_id: ret = utils.toggle_star(request, article_id)

    response_data = {}
    response_data['article_id'] = article_id
    response_data['result'] = ret
    return JsonResponse(response_data)


