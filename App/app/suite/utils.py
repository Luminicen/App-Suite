from django.http import HttpResponse
import requests
import mimetypes
mimetypes.init()

def obtenerTemplate(request):
    res= requests.get("https://guarded-falls-24810.herokuapp.com/template")
    return HttpResponse(res.content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
