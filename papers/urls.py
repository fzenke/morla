from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
            url(r'^$', views.index, name='index'),
            # ex: /polls/5/
            url(r'^(?P<article_id>[0-9]+)/$', views.detail, name='detail'),
            url(r'^all$', views.all, name='all'),
            url(r'^recent$', views.recent, name='recent'),
            url(r'^random$', views.random, name='random'),
            url(r'^suggested$', views.suggested, name='suggested'),
            url(r'^ham$', views.ham, name='ham'),
            url(r'^ham/upload$', views.upload_ham_bib_file, name='upload_ham_bib_file'),
            url(r'^spam$', views.spam, name='spam'),
            url(r'^starred$', views.starred, name='starred'),
            url(r'^login/$', auth_views.login, {'template_name': 'papers/login.html'}, name='login'),
            url(r'^logout/$', auth_views.logout, {'next_page': '/papers'}, name='logout'),
            url(r'^ajax_set_label/$', views.ajax_set_label, name='set_label'),
            url(r'^ajax_toggle_star/$', views.ajax_toggle_star, name='toggle_star')
]

