# Python
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from data.models import (
    UploadedFile,
    Sample,
    AbsorbanceProperties,
    AbsorbanceLocalMaximum,
    AbsorbanceData,
)


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "uploaded_at", "process_method")
    list_filter = ("process_method",)
    search_fields = ("original_name",)


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ("name", "uploaded_file")
    list_select_related = ("uploaded_file",)
    search_fields = ("name", "uploaded_file__original_name")
    list_filter = (("uploaded_file", admin.RelatedOnlyFieldListFilter),)
    autocomplete_fields = ("uploaded_file",)


class AbsorbanceLocalMaximumInline(admin.TabularInline):
    model = AbsorbanceLocalMaximum
    extra = 1


@admin.register(AbsorbanceProperties)
class AbsorbancePropertiesAdmin(admin.ModelAdmin):
    list_display = ("id", "sample", "wave_start", "wave_end", "data_points_link")
    list_select_related = ("sample",)
    search_fields = ("sample__name", "sample__uploaded_file__original_name")
    list_filter = (("sample", admin.RelatedOnlyFieldListFilter),)
    autocomplete_fields = ("sample",)
    inlines = [AbsorbanceLocalMaximumInline]

    def data_points_link(self, obj):
        url = reverse("admin:data_absorbancedata_changelist")
        url += f"?absorbance_properties__id__exact={obj.id}"
        count = obj.absorbancedata_set.count()
        return format_html('<a href="{}">{} záznamů</a>', url, count)

    data_points_link.short_description = "Spektrální data"


@admin.register(AbsorbanceLocalMaximum)
class AbsorbanceLocalMaximumAdmin(admin.ModelAdmin):
    list_display = ("id", "absorbance_properties", "sample", "wave_start", "wave_end", "maximum")
    list_select_related = ("absorbance_properties", "absorbance_properties__sample")
    search_fields = ("absorbance_properties__sample__name",)
    list_filter = (("absorbance_properties", admin.RelatedOnlyFieldListFilter),)

    def sample(self, obj):
        return obj.absorbance_properties.sample

    sample.admin_order_field = "absorbance_properties__sample__name"


@admin.register(AbsorbanceData)
class AbsorbanceDataAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "absorbance_properties",
        "sample",
        "wave_nm",
        "absorbance_au",
        "dark_counts",
        "ref_counts",
        "sample_counts",
    )
    list_select_related = ("absorbance_properties", "absorbance_properties__sample")
    search_fields = ("absorbance_properties__sample__name",)
    list_filter = (("absorbance_properties", admin.RelatedOnlyFieldListFilter),)
    autocomplete_fields = ("absorbance_properties",)
    ordering = ("wave_nm",)
    list_per_page = 100

    def sample(self, obj):
        return obj.absorbance_properties.sample

    sample.admin_order_field = "absorbance_properties__sample__name"