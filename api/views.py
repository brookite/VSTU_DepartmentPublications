import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api import settings
from api.utils import APIResponse
from core.vstulib import VSTULibrary
from api.serializers import *

from autoupdate.api import calculate_next_global_update
from autoupdate.api import calculate_next_update

logger = logging.getLogger("api")


class AuthorSuggestions(APIView):
    serializer_class = QuerySerializer

    def get(self, request):
        vstulib = VSTULibrary()
        serializer = self.serializer_class(
            data={"q": request.query_params.get("q", "")}
        )
        if serializer.is_valid():
            return Response(
                data=vstulib.get_author_suggestions(serializer.validated_data["q"])
            )
        else:
            return APIResponse(
                data=serializer.errors,
                status=400,
            )


class AuthorViewSet(viewsets.ViewSet):
    serializer_class = AuthorSerializer

    def list(self, request):
        authors = request.query_params.getlist("authors")
        authors = list(map(int, authors))
        queryset = Author.objects.filter(id__in=authors)
        serializer = self.serializer_class(queryset, many=True)
        return APIResponse(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def add(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            author = serializer.save()
            ShortUpdateTasks.objects.create(author=author)
            return APIResponse(serializer.data, status=status.HTTP_201_CREATED)
        return APIResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def search(self, request):
        input_serializer = self.serializer_class(data=request.query_params)
        if input_serializer.is_valid():
            queryset = Author.objects.filter(**input_serializer.validated_data)
            output_serializer = self.serializer_class(data=queryset, many=True)
            return APIResponse(output_serializer.data, status=status.HTTP_200_OK)
        return APIResponse(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def delete(self, request):
        id = request.data.get("id", "")
        if id:
            author = Author.objects.get(id=int(id))
            logger.debug(f"Удален автор: {author.full_name}")
            author.delete()
        return APIResponse(status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change(self, request):
        id = request.data.get("id", "")
        aliases = request.data.getlist("aliases")
        tags = request.data.getlist("tags")
        if "" in aliases:
            aliases.remove("")
        if "" in tags:
            tags.remove("")
        if not id:
            return APIResponse(
                message="id is required",
                status=status.HTTP_400_BAD_REQUEST,
            )
        author = Author.objects.get(pk=int(id))
        full_name = request.data.get("full_name", author.full_name)
        library_name = request.data.get("library_name", author.library_primary_name)
        department = request.data.get("department_id", author.department.id)
        author.full_name = full_name
        author.library_primary_name = library_name
        author.department = Department.objects.filter(id=department).first()
        author.tag_set.clear()
        for tag in list(map(lambda x: Tag.objects.get_or_create(name=x)[0], tags)):
            author.tag_set.add(tag)
        for alias in author.authoralias_set.all():
            alias.delete()
        for alias in list(
            map(
                lambda x: AuthorAlias.objects.get_or_create(alias=x, author=author)[0],
                aliases,
            )
        ):
            author.authoralias_set.add(alias)
        author.save()
        serializer = self.serializer_class(
            Author.objects.filter(pk=author.pk), many=True
        )
        return APIResponse(data=serializer.data)


class PublicationListView(ListAPIView):
    serializer_class = PublicationSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def get_queryset(self):
        queryset = Publication.objects.all()

        department_id = self.request.query_params.get("department")
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        added_date_from = self.request.query_params.get("added_date_from")
        if added_date_from:
            queryset = queryset.filter(
                added_date__gte=datetime.fromtimestamp(int(added_date_from))
            )

        added_date_to = self.request.query_params.get("added_date_to")
        if added_date_to:
            queryset = queryset.filter(
                added_date__lte=datetime.fromtimestamp(int(added_date_to))
            )

        assigned_to_department = self.request.query_params.get("assigned_to_department")
        if assigned_to_department:
            queryset = queryset.filter(department__isnull=False)

        tags = self.request.query_params.getlist("tags")
        tags = list(filter(lambda x: Tag.objects.filter(name=x).exists(), tags))
        tags = list(map(lambda x: Tag.objects.get_or_create(name=x)[0], tags))
        if tags:
            queryset = queryset.filter(tags__name__in=tags)

        author_id = self.request.query_params.get("author")
        if author_id:
            queryset = queryset.filter(authors__id=author_id)

        return queryset[:5120]


class FacultyDepartmentView(APIView):
    def get(self, request):
        faculties = Faculty.objects.all()
        departments = Department.objects.all()

        faculty_serializer = FacultySerializer(faculties, many=True)
        department_serializer = DepartmentSerializer(departments, many=True)

        return APIResponse(
            {
                "faculties": faculty_serializer.data,
                "departments": department_serializer.data,
            }
        )


class SettingsViewSet(viewsets.ViewSet):

    def list(self, request):
        settings = Settings.objects.all()
        result_dict = {}
        for setting in settings:
            result_dict[setting.param_name] = setting.param_value
        return APIResponse(result_dict)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change(self, request):
        changed_dict = request.data
        for key, value in changed_dict.items():
            if (obj := Settings.objects.filter(param_name=key)).exists():
                obj[0].param_value = value
                obj[0].save()
        return APIResponse(["Настройки успешно сохранены"], status=status.HTTP_200_OK)


class TagListView(ListAPIView):
    serializer_class = TagSerializer

    def list(self, request, *args, **kwargs):
        q = request.query_params.get("q")
        if q:
            queryset = Tag.objects.filter(name__icontains=q)
        else:
            queryset = Tag.objects.all()[: 10 * 1024]
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)


@api_view(["GET"])
def stats(request):
    stats = Timestamps.objects.all()
    result_dict = {}
    for stat in stats:
        result_dict[stat.param_name] = int(stat.timestamp.timestamp())

    last_author_update = settings.Timestamps().last_update
    if last_author_update:
        result_dict["last_author_update"] = int(last_author_update.timestamp())
    result_dict["next_global_update"] = int(calculate_next_global_update().timestamp())
    result_dict["next_update"] = int(calculate_next_update().timestamp())
    return APIResponse(result_dict)

@api_view(["POST"])
@login_required
def subscribe_email_toggle(request):
    email = request.POST.get("email")
    tags = request.POST.getlist("tags")
    tags = list(map(lambda x: Tag.objects.get_or_create(name=x)[0], tags))
    object, created = EmailSubscriber.objects.get_or_create(email=email)
    subscribe_status = True
    if not created or object.tags == tags:
        object.delete()
        subscribe_status = False
    else:
        object.tags.clear()
        for tag in tags:
            object.tags.add(tag)
    return APIResponse({"changed": True, "subscribe_status": subscribe_status})


class PlanViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def update_plan(self, request):
        update_interval = request.data["updateInterval"]
        day_of_week = request.data["dayOfWeek"]
        update_time = request.data["updateTime"].split(":")
        update_time = int(update_time[0]) * 3600 + int(update_time[1]) * 60
        if update_interval == "daily":
            interval, count = "day", 1
        elif update_interval == "weekly":
            interval, count = "week", 1
        elif update_interval == "monthly":
            interval, count = "month", 1
        elif update_interval == "biweekly":
            interval, count = "week", 2
        elif update_interval == "every_three_days":
            interval, count = "day", 3
        else:
            return APIResponse(
                message="Invalid data", status=status.HTTP_400_BAD_REQUEST
            )

        settingsobj = settings.Settings()
        logger.info(f"Запрос на смену плана автообновления с параметрами: {interval}, {count}, {day_of_week}, {update_time}")
        settingsobj.plan_autoupdate(interval, count, day_of_week, update_time)
        return APIResponse(status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def request_update(self, request):
        timestamps = settings.Timestamps()
        params = settings.Settings()
        result = timestamps.request_global_update()
        return APIResponse(data={"result": result, "update_interval": params.reschedule_minutes * 60}, status=status.HTTP_200_OK)