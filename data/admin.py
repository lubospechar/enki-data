from django.contrib import admin
from data.models import UploadedFile


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "uploaded_at", "process_method")
    list_filter = ("process_method",)
    search_fields = ("original_name",)
