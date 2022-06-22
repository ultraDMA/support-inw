from django.contrib import admin

from .models import *


class TicketInstanceAdmin(admin.ModelAdmin):
    pass


class TicketCommentAdmin(admin.ModelAdmin):
    pass


admin.site.register(TicketInstance, TicketInstanceAdmin)
admin.site.register(TicketComment, TicketCommentAdmin)
