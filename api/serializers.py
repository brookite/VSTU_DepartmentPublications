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

    def get_aliases(self, obj):
        author_aliases = AuthorAlias.objects.filter(author=obj)
        return [author_alias.alias for author_alias in author_aliases]

    def get_tags(self, obj):
        author_tags = obj.tag_set.all()
        return [tag.name for tag in author_tags]

    def get_last_updated(self, obj):
        last_updated = obj.last_updated
        return int(last_updated.timestamp()) if last_updated else None

    class Meta:
        model = Author
        fields = [
            "id",
            "full_name",
            "last_updated",
            "library_primary_name",
            "department_id",
            "aliases",
            "tags",
        ]
        read_only_fields = ["id", "last_updated", "aliases", "tags"]


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
