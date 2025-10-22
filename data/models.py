from django.db.models.functions import Cast
from django.db import models, transaction

import pandas as pd
import inspect
import os


class UploadedFile(models.Model):
    file = models.FileField(upload_to="upload/data/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_name = models.CharField(max_length=255, editable=False)
    process_method = models.CharField(max_length=100, choices=(), null=True, blank=True)

    def __str__(self):
        return self.original_name or (self.file.name if self.file else "")

    def update_original_name_from_file(self):
        if self.file and not self.original_name:
            self.original_name = os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        self.update_original_name_from_file()

        is_new = self._state.adding


        result = super().save(*args, **kwargs)

        if is_new and self.process_method:
            func = getattr(self, self.process_method, None)
            if callable(func):
                transaction.on_commit(lambda: func())

        return result


    def absorbance_dataframe(self, encoding: str = "utf-8"):
        if not self.file or not hasattr(self.file, "path"):
            raise ValueError("Soubor není dostupný na lokální cestě (self.file.path).")

        column_names = ["Wave_nm", "Dark_counts", "Ref_counts", "Sample_counts", "Absorbance_AU"]

        return pd.read_csv(
            self.file.path,
            sep=";",
            skiprows=7,
            header=None,
            names=column_names,
            engine="python",
            encoding=encoding,
        )

    def process_absorbance(self):
        new_sample = Sample(name="Sample", uploaded_file=self)
        new_sample.save()

        new_absorbance_properties = AbsorbanceProperties(sample=new_sample)
        new_absorbance_properties.save()

        data_frame = self.absorbance_dataframe()
        rows = data_frame.to_dict(orient="records")
        objs = [
            AbsorbanceData(
                absorbance_properties=new_absorbance_properties,
                wave_nm=float(r["Wave_nm"]),
                absorbance_au=float(r["Absorbance_AU"]),
                dark_counts=float(r["Dark_counts"]),
                ref_counts=float(r["Ref_counts"]),
                sample_counts=float(r["Sample_counts"]),
            )
            for r in rows
        ]

        AbsorbanceData.objects.bulk_create(objs, batch_size=1000)

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

class Sample(models.Model):
    name = models.CharField(max_length=255)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)

class AbsorbanceProperties(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    wave_start = models.FloatField(default=400.0)
    wave_end = models.FloatField(default=750.0)

    def __str__(self):
        return f"{self.sample.name} ({self.wave_start}-{self.wave_end})"

    def clean_data(self):
        return (
            self.absorbancedata_set
            .filter(wave_nm__gte=self.wave_start, wave_nm__lt=self.wave_end)
            .annotate(wave_nm_int=Cast("wave_nm", models.IntegerField()))
            .values("wave_nm_int")
            .annotate(avg_absorbance_au=models.Avg("absorbance_au"))
            .order_by("wave_nm_int")
        )




class AbsorbanceLocalMaximum(models.Model):
    absorbance_properties = models.ForeignKey(AbsorbanceProperties, on_delete=models.CASCADE)
    wave_start = models.FloatField()
    wave_end = models.FloatField()

    def maximum(self):
        return (self.absorbance_properties.clean_data()
                .filter(wave_nm_int__gte=self.wave_start, wave_nm_int__lt=self.wave_end)
                .order_by("-avg_absorbance_au")
                .first()
        )



class AbsorbanceData(models.Model):
    absorbance_properties = models.ForeignKey(AbsorbanceProperties, on_delete=models.CASCADE)
    wave_nm = models.FloatField()
    absorbance_au = models.FloatField()
    dark_counts = models.FloatField()
    ref_counts = models.FloatField()
    sample_counts = models.FloatField()

