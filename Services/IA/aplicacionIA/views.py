from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from aplicacionIA.models import *
from aplicacionIA.serializers import *
import json
import spacy
import os
import re
##########################################################################################################
#
# IA - EXPERIMENTAL - Extraccion de entidades
#
#~#######################################################################################################
def pantallaDePruebas(request):
    listado = request.GET.getlist('seleccionados')
    if request.method == "POST":
        #formulario = Entidades(request.POST)
        formulario = json.loads(request.POST)
        print(formulario)
        if formulario.is_valid():
            texto = formulario.cleaned_data["texto"]
            ner = spacy.load("es_core_news_lg")
            ner_custom = spacy.load("output/model-best")
            request.session["textoAI"] = texto
            doc = ner_custom(texto)
            doc2 = ner (texto)
            lista = set(doc.ents)#.union(set(doc2.ents))
            listado = []
            for i in lista:
                listado.append(str(i))
    elif (request.method == "GET") and listado:
        prediccionesErroneas(request)
        formulario = Entidades()
        listado = []
    else:
        listado = []
        formulario = Entidades()
    return render(request,'IA/pantallaTexto.html',{"form" : formulario,"tipo":listado, "marcados" : listado})
def extraerErrores(texto,inicio,fin,error):
    from spacy.tokens import Span
    from spacy.tokens import DocBin
    pos = 0
    poscionPunto = 0
    noEncontrePuntoAnteriorAlError = True
    for i in texto:
        if pos == inicio:
            noEncontrePuntoAnteriorAlError = False
            break
        elif i == "." and noEncontrePuntoAnteriorAlError:
            poscionPunto = pos
        pos += 1
    oracion = ""
    pos = 0
    OracionEncontrada = False
    for i in texto:
        if pos == poscionPunto:
            #print("ENCONTRO PUNTO")
            OracionEncontrada = True
        if (OracionEncontrada and i != "."):
            oracion = oracion + i
        elif (OracionEncontrada and i == "." and pos != poscionPunto):
            #print("SALIO")
            break
        pos +=1
    nlp = spacy.load("output/model-best")
    doc = nlp(oracion)
    doc.spans
    error_inicio=-1
    error_final=-1
    for i in doc.ents:
        if i.text == error:
            #print(i.start,i.end)
            error_inicio=i.start
            error_final=i.end
    #../ConfigTraining/Datos/trainPlantas.spacy
    entidades = None
    dbbin = DocBin().from_disk("app/ConfigTraining/Datos/trainUser.spacy")
    if (error_inicio != -1 or error_final != -1):
        doc.spans["incorrect_spans"] = [Span(doc,error_inicio,error_final,label = "Actor"),Span(doc,error_inicio,error_final,label = "Recurso")]
        dbbin.add(doc)
        dbbin.to_disk("app/ConfigTraining/Datos/trainUser.spacy")
        entidades = {
            "content" : oracion,
            "incorrect_spans" : [Span(doc,error_inicio,error_final,label = "Actor"),Span(doc,error_inicio,error_final,label = "Recurso")]
        }
    return entidades

def prediccionesErroneas(request):
    errores=[]
    if 'textoAI' in request.session:
        texto = request.session['textoAI']
        lista = []
        if 'seleccionados' in request.GET:
            lista = request.GET.getlist('seleccionados')
            print(lista)
            entidades = {
                "content" : texto,
                "entities" : []
            }
        for i in lista:
            #nesesito posicion del token
            match = (re.search(i, texto))
            print(i, match.start(), match.end())
            ent=extraerErrores(texto,match.start(),match.end(),i)
            errores.append(ent)
        import subprocess
        from moduloIa.settings import BASE_DIR
        #python -m spacy init fill-config base_config.cfg config
        #subprocess.run(["python","-m","spacy", "init","fill-config",os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','base_config.cfg') ,os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','config.cfg') ])
        #python -m spacy train config.cfg --output ./output --paths.train ./train.spacy --paths.dev ./dev.spacy
        subprocess.run(["python","-m","spacy","train",os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','config.cfg'),"--output","./output","--paths.train",os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','Datos','trainUser.spacy'),'--paths.dev',os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','Datos','trainPlantas.spacy')])
            
    #{"content":"El Ing. Agrónomo elige las semillas de tomate","entities":[[27,45,"Recurso",1,"rgb(15, 119, 46)"],[3,16,"Actor",0,"rgb(252, 2, 250)"]]}
def pantallaDeTaggeo(request):
    if request.method == "POST":
        formulario = Entidades(request.POST)
        if formulario.is_valid():
            print(formulario.cleaned_data["texto"])
            from moduloIa.settings import BASE_DIR
            f = open(os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','Datos','datasetUsuario.json'),'r', encoding = 'utf-8')
            archivo = f.read()
            f.close()
            archivoDesj=json.loads(archivo)
            archivoDesj.append(json.loads(formulario.cleaned_data["texto"]))
            print(archivoDesj)
            with open(os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','Datos','datasetUsuario.json'),'w',encoding = 'utf-8') as f:
                f.write(json.dumps(archivoDesj))

        formulario = Entidades()
    else:
        formulario = Entidades()
    return render(request,'IA/pantallaDeTaggeo.html',{"form" : formulario})