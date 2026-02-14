from django.contrib import admin

from api.models import (
    Author,
    AuthorAlias,
    Department,
    EmailSubscriber,
    Faculty,
    Publication,
    Settings,
    Tag,
)


class AuthorAdmin(admin.ModelAdmin):
    search_fields = ("full_name", "library_primary_name", "department")
    list_display = ("full_name", "library_primary_name", "department")
    exclude = ("last_updated",)


class PublicationAdmin(admin.ModelAdmin):
    search_fields = ("html_content", "department", "authors")
    list_display = ("html_content", "department")
    exclude = ("added_date",)


admin.site.register(Author, AuthorAdmin)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(Department)
admin.site.register(Faculty)
admin.site.register(Settings)
admin.site.register(Tag)
admin.site.register(EmailSubscriber)
admin.site.register(AuthorAlias)
