import re
from pstats import Stats

from rest_framework import serializers
from rest_framework.views import APIView

from .models import *


class QuerySerializer(serializers.Serializer):
    q = serializers.CharField(max_length=128, default="")


class AuthorSerializer(serializers.ModelSerializer):
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="department", required=False
    )
    aliases = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()

    aliases_list = serializers.ListField(required=False)
    tags_list = serializers.ListField(required=False)

    def get_aliases(self, obj):
        author_aliases = AuthorAlias.objects.filter(author=obj)
        return [author_alias.alias for author_alias in author_aliases]

    def get_tags(self, obj):
        author_tags = obj.tag_set.all()
        return [tag.name for tag in author_tags]

    def get_last_updated(self, obj):
        last_updated = obj.last_updated
        return int(last_updated.timestamp()) if last_updated else None

    def validate_library_primary_name(self, value):
        library_name_regex = re.compile(r"^([\(\)\w-]{1,30})\s+([\(\)\w-]{1,5})\s{0,}\.\s{0,}([\(\)\w-]{1,5})\s?\.?$")
        if not (match := library_name_regex.match(value)):
            raise serializers.ValidationError("Неверно заданы фамилия и инициалы для библиотеки. Правильный формат: \"Иванов И.И.\"")
        else:
            return f"{match.group(1)} {match.group(2)}.{match.group(3)}."

    def create(self, validated_data):
        aliases_data = validated_data.pop("aliases_list", [])
        tags_data = validated_data.pop("tags_list", [])
        validated_data.pop("added", [])
        validated_data.pop("last_updated", [])
        author = Author.objects.create(**validated_data)

        for alias in aliases_data:
            AuthorAlias.objects.create(author=author, alias=alias)
        for tag in tags_data:
            tag = Tag.objects.get_or_create(name=tag)[0]
            author.tag_set.add(tag)
        author.save()

        return author

    def update(self, instance, validated_data):
        aliases_data = validated_data.pop("aliases_list", [])
        tags_data = validated_data.pop("tags_list", [])
        validated_data.pop("added", [])
        validated_data.pop("last_updated", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.aliases.all().delete()
        instance.tags.all().delete()
        AuthorAlias.objects.filter(author=instance).delete()
        for alias in aliases_data:
            AuthorAlias.objects.create(author=instance, alias=alias)
        Tag.objects.filter(authors__in=[instance]).delete()
        for tag in tags_data:
            tag = Tag.objects.get_or_create(name=tag)
            instance.tag_set.add(tag)
        instance.save()

        return instance

    class Meta:
        model = Author
        fields = [
            "id",
            "full_name",
            "last_updated",
            "added",
            "library_primary_name",
            "department_id",
            "aliases",
            "tags",
            "aliases_list",
            "tags_list",
        ]
        read_only_fields = ["id", "last_updated", "added", "aliases", "tags"]


class DepartmentSerializer(serializers.ModelSerializer):
    faculty_id = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all(), source="faculty", required=False
    )

    class Meta:
        model = Department
        fields = ["id", "name", "faculty_id"]


class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ["id", "name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class PublicationSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True)
    # TODO: may be many department support
    department = DepartmentSerializer()

    added_date = serializers.SerializerMethodField()

    def get_added_date(self, obj):
        added_date = obj.added_date
        return int(added_date.timestamp()) if added_date else None

    class Meta:
        model = Publication
        fields = ["authors", "html_content", "added_date", "department"]
