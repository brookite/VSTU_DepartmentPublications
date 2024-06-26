# Generated by Django 5.0.4 on 2024-04-27 11:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_alter_author_full_name_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="author",
            name="department",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="api.department",
                verbose_name="Кафедра",
            ),
        ),
        migrations.AlterField(
            model_name="author",
            name="full_name",
            field=models.CharField(max_length=255, verbose_name="ФИО"),
        ),
        migrations.AlterField(
            model_name="author",
            name="last_updated",
            field=models.DateTimeField(null=True, verbose_name="Последнее обновление"),
        ),
        migrations.AlterField(
            model_name="author",
            name="library_primary_name",
            field=models.CharField(
                max_length=128, verbose_name="Инициалы для библиотеки (главные)"
            ),
        ),
        migrations.AlterField(
            model_name="authoralias",
            name="alias",
            field=models.CharField(
                max_length=128, verbose_name="Дополнительные инициалы для библиотеки"
            ),
        ),
        migrations.AlterField(
            model_name="authoralias",
            name="author",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="api.author",
                verbose_name="Автор",
            ),
        ),
        migrations.AlterField(
            model_name="department",
            name="faculty",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="api.faculty",
                verbose_name="Факультет",
            ),
        ),
        migrations.AlterField(
            model_name="department",
            name="library_id",
            field=models.IntegerField(verbose_name="ID в библиотеке"),
        ),
        migrations.AlterField(
            model_name="department",
            name="name",
            field=models.CharField(max_length=255, verbose_name="Название"),
        ),
        migrations.AlterField(
            model_name="emailsubscriber",
            name="email",
            field=models.CharField(max_length=96, verbose_name="E-mail"),
        ),
        migrations.AlterField(
            model_name="emailsubscriber",
            name="tags",
            field=models.ManyToManyField(to="api.tag", verbose_name="Теги"),
        ),
        migrations.AlterField(
            model_name="faculty",
            name="library_id",
            field=models.IntegerField(verbose_name="ID в библиотеке"),
        ),
        migrations.AlterField(
            model_name="faculty",
            name="name",
            field=models.CharField(max_length=128, verbose_name="Название"),
        ),
        migrations.AlterField(
            model_name="publication",
            name="added_date",
            field=models.DateTimeField(
                auto_now_add=True, verbose_name="Дата обновления"
            ),
        ),
        migrations.AlterField(
            model_name="publication",
            name="authors",
            field=models.ManyToManyField(to="api.author", verbose_name="Авторы"),
        ),
        migrations.AlterField(
            model_name="publication",
            name="department",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="api.department",
                verbose_name="Кафедра",
            ),
        ),
        migrations.AlterField(
            model_name="publication",
            name="html_content",
            field=models.TextField(verbose_name="HTML-название публикации"),
        ),
        migrations.AlterField(
            model_name="settings",
            name="param_name",
            field=models.CharField(
                max_length=64,
                primary_key=True,
                serialize=False,
                unique=True,
                verbose_name="Название",
            ),
        ),
        migrations.AlterField(
            model_name="settings",
            name="param_value",
            field=models.CharField(
                max_length=1024, null=True, verbose_name="Настройка"
            ),
        ),
        migrations.AlterField(
            model_name="tag",
            name="authors",
            field=models.ManyToManyField(to="api.author", verbose_name="Авторы"),
        ),
        migrations.AlterField(
            model_name="tag",
            name="name",
            field=models.CharField(max_length=48, verbose_name="Название"),
        ),
    ]
