from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from aplicacionIA.models import *
from aplicacionIA.serializers import *
# Create your views here.
