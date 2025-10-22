# Python
from django.db import models
import inspect


class UploadedFile(models.Model):
    file = models.FileField(upload_to="upload/data/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_name = models.CharField(max_length=255, editable=False)
    process_method = models.CharField(max_length=100, choices=(), null=True, blank=True)

    def __str__(self):
        return self.original_name

    def process_absorbance(self):
        pass

    def process_ph(self):
        pass

    @classmethod
    def get_process_method_choices(cls):
        methods = []
        for name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name.startswith("process_"):
                label = name[len("process_"):]
                methods.append((name, label))
        return methods

    class Meta:
        ordering = ['-uploaded_at']

UploadedFile._meta.get_field("process_method").choices = UploadedFile.get_process_method_choices()