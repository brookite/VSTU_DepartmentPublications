from typing import TYPE_CHECKING

from django.db import models
from django.db.models import ManyToManyField

class Faculty(models.Model):
    name = models.CharField(max_length=128, verbose_name="Название")
    library_id = models.IntegerField(verbose_name="ID в библиотеке")

    class Meta:
        verbose_name = "Факультет"
        verbose_name_plural = "Факультеты"

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    faculty = models.ForeignKey(
        Faculty, on_delete=models.CASCADE, verbose_name="Факультет"
    )
    library_id = models.IntegerField(verbose_name="ID в библиотеке")

    class Meta:
        verbose_name = "Кафедра"
        verbose_name_plural = "Кафедры"

    def __str__(self):
        return self.name


class Author(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(null=True, verbose_name="Последнее обновление")
    library_primary_name = models.CharField(
        max_length=128, verbose_name="Инициалы для библиотеки (главные)"
    )
    department = models.ForeignKey(
        Department, null=False, on_delete=models.RESTRICT, verbose_name="Кафедра"
    )
    if TYPE_CHECKING:
        from django.db.models.manager import RelatedManager

        tag_set: RelatedManager["Tag"]
        authoralias_set: RelatedManager["AuthorAlias"]

    class Meta:
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"

    def __str__(self):
        return self.full_name


class AuthorAlias(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name="Автор")
    alias = models.CharField(
        max_length=128, verbose_name="Дополнительные инициалы для библиотеки"
    )

    class Meta:
        verbose_name = "Псевдоним автора"
        verbose_name_plural = "Псевдонимы автора"

    def __str__(self):
        return self.alias


class Tag(models.Model):
    name = models.CharField(max_length=48, verbose_name="Название", unique=True)
    authors = ManyToManyField(Author, verbose_name="Авторы")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Publication(models.Model):
    authors = ManyToManyField(Author, verbose_name="Авторы")
    html_content = models.TextField(verbose_name="HTML-название публикации")
    added_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата обновления")
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Кафедра",
    )
    sort_order = models.IntegerField(verbose_name="Поле сортировки (год публикации)", null=False, default=0)

    class Meta:
        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"

    def __str__(self):
        return self.html_content



class EmailSubscriber(models.Model):
    email = models.CharField(max_length=96, verbose_name="E-mail")
    tags = models.ManyToManyField(Tag, verbose_name="Теги")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Подписчик на обновления"
        verbose_name_plural = "Подписчики на обновления"

    def __str__(self):
        return self.email


class Timestamps(models.Model):
    param_name = models.CharField(max_length=64, primary_key=True, unique=True)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.param_name} -> {self.timestamp}"


class ShortUpdateTasks(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return str(self.author)


class Settings(models.Model):
    param_name = models.CharField(
        max_length=64, primary_key=True, unique=True, verbose_name="Название"
    )
    param_value = models.CharField(max_length=1024, null=False, verbose_name="Настройка")

    class Meta:
        verbose_name = "Параметр системы"
        verbose_name_plural = "Параметры системы"


    def __str__(self):
        return self.param_name
