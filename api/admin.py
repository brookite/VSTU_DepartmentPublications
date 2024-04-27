from django.contrib import admin

from api.models import *

admin.site.register(Author)
admin.site.register(Publication)
admin.site.register(Department)
admin.site.register(Faculty)
admin.site.register(Settings)
admin.site.register(Tag)
admin.site.register(EmailSubscriber)
admin.site.register(AuthorAlias)
