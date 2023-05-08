from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from aplicacionIA.models import *
from aplicacionIA.serializers import *
from moduloIa.settings import BASE_DIR as direccion_base
import json
import spacy
import os
import re
##########################################################################################################
#
# IA - EXPERIMENTAL - Extraccion de entidades
# Debe tener texto en el campo!
#
#~#######################################################################################################
@csrf_exempt
def procesarTexto(request):
    """ 
        Recibe algo del tipo "nombre" y "texto", lo procesa y devuelve entidades
        Si no encuentra el texto devuelve 409
    """
    data = "hola mundo"
    if request.method == "POST":
        #formulario = Entidades(request.POST)
        #print("DATOS RECIBIDOS")
        #print(json.loads(request.body))
        formulario = request.body
        
        if formulario:
            texto = json.loads(formulario)["texto"]
            ner_custom = spacy.load(os.path.join(os.path.dirname(direccion_base),"IA","aplicacionIA","output","model-best" ))
            request.session["textoAI"] = texto
            doc = ner_custom(texto)
            lista = set(doc.ents)
            listado = []
            for i in lista:
                listado.append(str(i))
            data = listado
        else:
            data = "No respeta el formato"
            return HttpResponse(json.dumps(data, indent=4, sort_keys=True), status=409)
    else:
        listado = []
        #formulario = Entidades()
    return HttpResponse(json.dumps(data, indent=4, sort_keys=True), content_type="application/json")

def extraerErrores(texto,inicio,fin,error):
    """
    Encuentra los errores y los carga en el bin del modelo para dar feedback negativo
    """
    from spacy.tokens import Span
    from spacy.tokens import DocBin
    pos = 0
    poscionPunto = 0
    noEncontrePuntoAnteriorAlError = True
    #busco la oracion conflictiva
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
            OracionEncontrada = True
        if (OracionEncontrada and i != "."):
            oracion = oracion + i
        elif (OracionEncontrada and i == "." and pos != poscionPunto):
            break
        pos +=1
    #proceso el error para dar feedback negativo al modelo
    nlp = spacy.load(os.path.join(os.path.dirname(direccion_base),"IA","aplicacionIA","output","model-best"))
    doc = nlp(oracion)
    doc.spans
    error_inicio=-1
    error_final=-1
    for i in doc.ents:
        if i.text == error:
            error_inicio=i.start
            error_final=i.end
    entidades = None
    dbbin = DocBin().from_disk(spacy.load(os.path.join(os.path.dirname(direccion_base),"IA","aplicacionIA","DatosYConfiguracionDeEntrenamiento","Datos","trainUser.spacy")))
    if (error_inicio != -1 or error_final != -1):
        doc.spans["incorrect_spans"] = [Span(doc,error_inicio,error_final,label = "Actor"),Span(doc,error_inicio,error_final,label = "Recurso")]
        dbbin.add(doc)
        dbbin.to_disk(os.path.join(os.path.dirname(direccion_base),"IA","aplicacionIA","DatosYConfiguracionDeEntrenamiento","Datos","trainUser.spacy"))
        entidades = {
            "content" : oracion,
            "incorrect_spans" : [Span(doc,error_inicio,error_final,label = "Actor"),Span(doc,error_inicio,error_final,label = "Recurso")]
        }
    return entidades
@csrf_exempt
def prediccionesErroneas(request):
    """
    Recibe una serie de palabras y el texto para reentrenar a la ia y corregir las predicciones erroneas
    """
    errores=[]
    print(request.body)
    resp = json.loads(request.body)
    texto = resp["texto"]
    lista = resp["sel"]
    lista = []
    if lista:
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
        #Arranco un entrenamiento
    import subprocess
    from moduloIa.settings import BASE_DIR
                #os.path.dirname(direccion_base),"IA","aplicacionIA","output","model-best"
    subprocess.run(["python","-m","spacy","train",os.path.join(os.path.dirname(direccion_base),"IA","aplicacionIA",'config.cfg'),"--output","./output","--paths.train",os.path.join(os.path.dirname(direccion_base),"IA","aplicacionIA","DatosYConfiguracionDeEntrenamiento","Datos","trainUser.spacy"),'--paths.dev',os.path.join(os.path.dirname(direccion_base),"IA","aplicacionIA","DatosYConfiguracionDeEntrenamiento","Datos","trainPlantas.spacy"),'--paths.modelos',os.path.join(os.path.dirname(direccion_base),"IA","aplicacionIA",'Modelo_entrenado')])
    return HttpResponse(json.dumps("OK"), status=200) 
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