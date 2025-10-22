from io import BytesIO
from django.http import Http404, HttpResponse
from django.views import View
from openpyxl import Workbook
from data.models import AbsorbanceProperties

class CleanDataXlsxView(View):
    def get(self, request, pk):
        try:
            props = AbsorbanceProperties.objects.get(pk=pk)
        except AbsorbanceProperties.DoesNotExist:
            raise Http404("Záznam nenalezen.")

        wb = Workbook()
        ws = wb.active
        ws.title = "clean_data"

        ws.append(["wave_nm", "avg_absorbance_au"])

        for row in props.clean_data():
            ws.append([row["wave_nm_int"], row["avg_absorbance_au"]])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="data_id-{props.pk}.xlsx"'
        return response
