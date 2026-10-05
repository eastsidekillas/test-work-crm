from django.contrib import admin
from .models import Lead, Tag

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["name", "contact", "source", "created_at"]
    list_filter = ["source", "tags"]
    search_fields = ["name", "contact", "request"]
    filter_horizontal = ["tags"]
    readonly_fields = ["submission_id", "telegram_user_id", "telegram_chat_id", "created_at", "updated_at"]

admin.site.register(Tag)
