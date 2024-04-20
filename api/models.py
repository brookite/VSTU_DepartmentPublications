from django.db import models
from django.db.models import ManyToManyField


class Faculty(models.Model):
    name = models.CharField(max_length=96)
    library_id = models.IntegerField()


class Department(models.Model):
    name = models.CharField(max_length=96)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    library_id = models.IntegerField()


class Author(models.Model):
    full_name = models.CharField(max_length=128)
    last_updated = models.DateTimeField(auto_now=True)
    library_primary_name = models.CharField(max_length=96)
    department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL)


class AuthorAlias(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    alias = models.CharField(max_length=96)


class Tag(models.Model):
    name = models.CharField(max_length=32)
    authors = ManyToManyField(Author)


class Publication(models.Model):
    authors = ManyToManyField(Author)
    html_content = models.TextField()
    added_date = models.DateTimeField(auto_now_add=True)
    department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL)


class EmailSubscriber(models.Model):
    email = models.CharField(max_length=96)
    tags = models.ManyToManyField(Tag)