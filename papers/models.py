from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Article(models.Model):
    title = models.CharField(max_length=250)
    authors = models.CharField(max_length=500)
    pubdate = models.DateField()
    journal = models.CharField(max_length=250)
    abstract = models.TextField()
    keywords = models.CharField(max_length=250, blank=True)
    url = models.URLField(blank=True)
    doi = models.CharField(max_length=128, blank=True)
    pmid = models.IntegerField(null=True, blank=True)
    # source = models.ForeignKey(Source, on_delete=models.CASCADE)
    date_added = models.DateTimeField( )

    def __str__(self):
        return "%s (%s). %s." % (self.authors, self.pubdate, self.title)


class Feature(models.Model):
    id = models.BigAutoField(primary_key=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    index = models.IntegerField()
    value = models.FloatField()

    class Meta:
        unique_together = ('article', 'index')

    def __str__(self):
        return "<Feature(index=%i, value=%f)>" % (self.index, self.value)


class Similarity(models.Model):
    id = models.BigAutoField(primary_key=True)
    a = models.ForeignKey(Article, related_name='a', on_delete=models.CASCADE)
    b = models.ForeignKey(Article, related_name='b', db_index=False, on_delete=models.CASCADE)
    value = models.FloatField()

    class Meta:
        unique_together = (("a", "b"),) 

    def __str__(self):
        return "<Similarity(a=%i, b=%i, value=%f)>" % (self.a.id, self.b.id, self.value)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    spam = models.ManyToManyField(Article, related_name='spam')
    ham  = models.ManyToManyField(Article, related_name='ham')
    starred  = models.ManyToManyField(Article, related_name='starred')
    suggested = models.ManyToManyField(Article, related_name='suggested', through='Recommendation')
    last_traindata_update = models.DateTimeField( )
    last_prediction_run = models.DateTimeField( )

    def __str__(self):
        return "<Profile (id=%i)>" % (self.id)


class Recommendation(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date_added = models.DateTimeField( )

    def __str__(self):
        return "<Recommendation(profile=%i, article=%i)>" % (self.profile.id, self.article.id)
