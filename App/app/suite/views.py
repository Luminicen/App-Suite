from io import StringIO
import mimetypes
import os
import re
from cgitb import text
from MySQLdb import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from app.settings import STATICFILES_DIRS
from suite.models import *
from suite.forms import *
import json
from suite.ontoscen.wikilink import Wikilink
from suite.ontoscen.ontoscen import Ontoscen
from suite.ontoscen.requirement import Requirement
import spacy
import requests
from spacy.matcher import Matcher
from django.views.decorators.cache import cache_control
nlp = spacy.load("es_dep_news_trf")
#from django.contrib.auth import authenticate, login
from rest_framework import viewsets
from suite.serializers import ArtefactoSerializer
#IA
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import string
import gensim
from gensim import corpora
import pandas as pd
from nltk import *
# Create your views here.
############################### Permisos ##########################################
# Codigos de los permisos
####################################################################################
def tienePermiso(user,proyecto):
    if (proyecto.owner==user) or (user in proyecto.participantes.all()):
        return True
    return False
def puedeEscribirEnBd(user,id):
    #solucion momentanea a la concurrencia
    #si la ultima modificacione es mas vieja que hace 20 segundos entonses puedo escribir
    concu=Concurrencia.objects.get(nombre=user.username)
    if Artefacto.objects.get(id=id).texto == concu.texto_anterior:
        return True
    return False
def eliminarConcurrencia(user):
    for i in Concurrencia.objects.filter(nombre=user.username):
        i.delete()
############################### Proyectos ##########################################
# En este lugar estaran todos los codigos del modulo de proyectos
####################################################################################
def proyectos(request):
    #obtengo todos los proyectos y filtro por los que son mios
    proyectos=Proyecto.objects.all()
    mio=[]
    ok=False
    usuario=request.user
    for p in proyectos:
        if p.owner==usuario:
            mio.append(p)
            ok=True
    otros=[]
    for p in proyectos:
        if (usuario in p.participantes.all()):
            otros.append(p)
    #print(otros)
    return render(request,'proyectos.html',{"ok":ok,"proyectos":mio,"otro_p":otros})

def crearProyecto(request):
    #creo el formulario proyecto y lo mando al template
    #si el form tiene datos invalidos creo el objeto y guardo en bd
    if request.method == "POST":
        formulario = ProyectoForm(request.POST)
        if formulario.is_valid():
            print(formulario)
            formulario.save()   
            return redirect(reverse('proyectos')) 
    else: 
        formulario = ProyectoForm(instance=request.user)
    return render(request, "proyecto-crear_conParticipantes.html", {"form" : formulario})
def eliminarProyecto(request,id):
    #obtengo el proyecto a eliminar por id y lo elimino
    proyecto=Proyecto.objects.get(id=id)
    if request.user != proyecto.owner:
        return HttpResponse("NO SOS EL OWNER")
    try:
        proyecto.delete()
    except IntegrityError as e:
        return HttpResponse("ha ocurrido un error")
    return redirect(reverse('proyectos'))

def modificarProyecto(request,id):
    #obtengo los datos del proyecto por id
    #mando los datos del proyecto con el form
    #solamente modifica el nombre
    proyecto=Proyecto.objects.get(id=id)
    if request.method == "POST":
        formulario = ProyectoForm(request.POST)
        if formulario.is_valid():
            infForma=formulario.cleaned_data
            proyecto.titulo=infForma['titulo']
            proyecto.participantes.set(infForma['participantes'])
            proyecto.save()   
            return redirect(reverse('proyectos')) 
    else:
        datosAModificar={'titulo': proyecto.titulo,'owner':proyecto.owner,'participantes':proyecto.participantes.all()}
        formulario = ProyectoForm(datosAModificar,instance=request.user,initial=datosAModificar)
    return render(request, "proyecto-crear_conParticipantes.html", {"form" : formulario})


############################### arte4facto ##########################################
# En este lugar estaran todos los codigos del modulo de artefacto
####################################################################################
def artefactos(request,id):
    proyecto=Proyecto.objects.get(id=id)
    escen= proyecto.artefactos.all()
    if not tienePermiso(request.user,proyecto):
        return render(request,'ERRORES/403.html',{})
    eliminarConcurrencia(request.user)
    ok=False
    form=ElejirArtefactoAcrear()
    form2=Busqueda()
    if escen:
        ok=True
    if request.method == "POST":
        formulario = ElejirArtefactoAcrear(request.POST)
        if formulario.is_valid():
            infForma=formulario.cleaned_data
            idT=TipoDeArtefacto.objects.get(id=infForma['eleccion']).id
            idP=proyecto.id
            return redirect(reverse('crearArtefactos',kwargs={'idP':idP,'idT':idT}))
    elif request.method == "GET":
        #print(request.GET)
        if 'buscar' in request.GET:
            fil=TipoDeArtefacto.objects.get(id=request.GET['buscar'])
            aux=[]
            for i in escen:
                if i.tipoDeArtefacto == fil:
                    aux.append(i)
            escen=aux
        sel = request.GET.getlist('seleccionados')
        funcionalidad=funcionalidadesRegitradas(request,sel,id)
        if funcionalidad == 'kg':
            tipo=TipoDeArtefacto.objects.get(tipo="KnowledgeGraph")
            fields=[]
            fields.append("NONE")
            return redirect(reverse('crearKG',kwargs={'idP':id}))
        elif funcionalidad=="cskw":
            return redirect(reverse('artefactos',kwargs={'id':id}))
        elif funcionalidad=="uml":
            return redirect(reverse('crearUML',kwargs={'idP':id}))
        elif funcionalidad=="exportSKW" :
            aTxt=request.session["textoTxt"]
            response = HttpResponse(content_type='text/plain')  
            response['Content-Disposition'] = 'attachment; filename="keyWordsDeLosEscenarios.txt"'
            response.write(aTxt)
            return response
        elif funcionalidad=="shacl4j":
            aTxt=request.session["textoTxt"]
            response = HttpResponse(content_type='text/plain')  
            response['Content-Disposition'] = 'attachment; filename="reporte.txt"'
            response.write(aTxt)
            return response
    botones=listaBotones()
    return render(request,'artefactos-lista.html',{"artifacts":escen,"ok":ok,"form":form,"formB":form2,"idP":id,"botones":botones})
def tipoForm(tipo,val):
    #elegirTipo
    #debe estar tal cual esta cargado en la BD
    formulario=None
    formulario=globals()[tipo.tipo]().formulario(val)
    if formulario==None:
        raise("TE OLVIDASTE DE DECLARAR EL OBJETO DEL FORM ")
    return formulario
def convertidorDeForms(tipo,form,usr):
    #transformo los fomularios a un texto X
    texto=None
    aux=json.dumps(form,indent=4)
    texto=Artefacto(nombre=form['nombre'],texto=aux,owner=usr,tipoDeArtefacto=tipo)
    return texto

def verArtefactos(request, id):
    artefacto=Artefacto.objects.get(id=id)
    return render(request, "ver.html", {"artefacto" : artefacto})

def crearArtefactos(request,idP,idT):
    #idP = id del Proyecto
    #idT = id del Tipo
    proyecto=Proyecto.objects.get(id=idP)
    if not tienePermiso(request.user,proyecto):
        return render(request,'ERRORES/403.html',{})
    tipo=TipoDeArtefacto.objects.get(id=idT)
    if request.method == "POST":
        if (request.FILES):
            response= requests.post("https://guarded-falls-24810.herokuapp.com/graph", files={"file": request.FILES["file"]})
            a= Artefacto(nombre=request.POST["nombre"],texto=response.text,owner=request.user,tipoDeArtefacto=tipo)
            a.save()
            proyecto.artefactos.add(a)
            proyecto.save()
            return redirect(reverse('artefactos',kwargs={'id':idP}))
            
        else:
            formulario = form=tipoForm(tipo,request.POST)
            if formulario.is_valid():
                infForma=formulario.cleaned_data
                texto=convertidorDeForms(tipo,infForma,request.user)  
                texto.save()
                proyecto.artefactos.add(texto)
                proyecto.save()
                return redirect(reverse('artefactos',kwargs={'id':idP}))
    else:
        #uso None para inicializar un form vacio
        form=tipoForm(tipo,None)

    all_fields = form.declared_fields.keys()
    fields=[]
    for i in all_fields:
        if i != 'nombre':
            fields.append('id_'+i)
    return render(request, "proyecto-crear.html", {"form" : form,"campos":fields,"tipo":tipo.tipo,"idP":idP})

@cache_control(no_cache=True, must_revalidate=True)
def modificarArtefacto(request,id,idP):
    proyecto = Proyecto.objects.get(id=idP)
    if not tienePermiso(request.user,proyecto):
        return render(request,'ERRORES/403.html',{})
    artefacto= Artefacto.objects.get(id=id)
    texto=json.loads(artefacto.texto)
    no_escribir=False
    if request.method == "POST" and Concurrencia.objects.filter(nombre=request.user.username):
        formulario = form=tipoForm(artefacto.tipoDeArtefacto,request.POST)
        if formulario.is_valid():
            infForma=formulario.cleaned_data
            aux=json.dumps(infForma,indent=4)
            artefacto.nombre=infForma['nombre']
            artefacto.texto=aux
            #recurrencia

            if puedeEscribirEnBd(request.user,id):
                concu=Concurrencia.objects.get(nombre=request.user.username)
                concu.delete()
                artefacto.save()
                return redirect(reverse('artefactos',kwargs={'id':idP}))
            else:
                no_escribir=True
                concu=Concurrencia.objects.get(nombre=request.user.username)
                concu.delete()
    else:
        #uso None para inicializar un form vacio
        form=tipoForm(artefacto.tipoDeArtefacto,texto)
        conc=Concurrencia.objects.filter(nombre=request.user.username)
        if conc:
            eliminarConcurrencia(request.user)
        concu=Concurrencia(nombre=request.user.username,texto_anterior=artefacto.texto)
        concu.save()
    #queda llenar el form y mandarlo como siempre
    all_fields = form.declared_fields.keys()
    fields=[]
    for i in all_fields:
        if i != 'nombre':
            fields.append('id_'+i)
    return render(request, "proyecto-modificar.html", {"form" : form,"campos":fields,"tipo":artefacto.tipoDeArtefacto.tipo,"no_escribir":no_escribir,"id":id,"idP":idP})

def destruirArtefacto(request,id,idP):
    artefacto= Artefacto.objects.get(id=id)
    proyecto= Proyecto.objects.get(id=idP)
    if not tienePermiso(request.user,proyecto):
        return render(request,'ERRORES/403.html',{})
    proyecto.artefactos.remove(artefacto)
    artefacto.delete()
    return redirect(reverse('artefactos',kwargs={'id':idP}))

def get_all_fields_from_form(instance):
    """"
    Return names of all available fields from given Form instance.

    :arg instance: Form instance
    :returns list of field names
    :rtype: list
    """

    fields = list(instance().base_fields)

    for field in list(instance().declared_fields):
        if field not in fields:
            fields.append(field)
    return fields
def crearArtefactoKG(request,idP):
    #idP = id del Proyecto
    #idT = id del Tipo
    #print("ENTRO A CREAR ARTEFACTOKG")
    proyecto=Proyecto.objects.get(id=idP)
    tipo=TipoDeArtefacto.objects.get(tipo='KnowledgeGraph')
    if request.method == "POST":
        formulario = KnowledgeGraphs(request.POST)
        if formulario.is_valid():
            infForma=formulario.cleaned_data
            texto=convertidorDeForms(tipo,infForma,request.user)  
            texto.save()
            proyecto.artefactos.add(texto)
            proyecto.save()
            return redirect(reverse('artefactos',kwargs={'id':idP}))
    else:
        file=open("data/output.ttl", mode="r", encoding="utf-8")
        data={'graphOutput': file.read()}
        form=KnowledgeGraphs(data)
    all_fields = form.declared_fields.keys()
    fields=[]
    for i in all_fields:
        if i != 'nombre':
            fields.append('id_'+i)
    return render(request, "proyecto-crear_conParticipantes.html", {"form" : form,"campos":fields,"tipo":tipo.tipo})

def crearArtefactoUML(request, idP):
    #aTxt=request.session["UMLDATA"]
    data = request.session["UMLDATA"]
    #print(data)
    context = {}
    try:
        static_url = STATICFILES_DIRS[0]
        filename = os.path.join(static_url, "uml", f"uml_{idP}.txt")
        file = open(filename, "w")
        file.write("@startuml\n")

        for clase in data:
            nombre_clase = str(clase["nombre"]).capitalize()
            file.write("class " + nombre_clase + "\n")
            try:
                for atributo in clase["atributos"]:
                    file.write(f"{nombre_clase} : {atributo}" + "\n")
            except:
                pass
            try:
                for relacion in clase["relaciones"]:
                    relacion = str(relacion).capitalize()
                    file.write(f"{nombre_clase} --> {relacion}" + "\n")
            except:
                pass
            try:
                for metodo in clase["metodos"]:
                    file.write(f"{nombre_clase} : {metodo}()" + "\n")
            except:
                pass
            try:
                for subclase in clase["subclases"]:
                    subclase = str(subclase).capitalize()
                    file.write(f"{nombre_clase} <|-- {subclase}" + "\n")
            except:
                pass

        file.write("@enduml")
        file.close()

        os.system(f"java -jar {static_url}/plantuml.jar {static_url}/uml/uml_{idP}.txt")

    except Exception as e:
        context["error"] = str(e)
        print(e)

    context["img_name"] = f"uml_{idP}.png"
    return render(request, 'uml-visualizer.html', context=context)

############################### TESTE ##########################################
# TEST API# os.system("java -jar plantuml.jar test.txt")
####################################################################################

###########################################################################################
#CLASES
#PARA APROBECHAR POLIMORFISMO
#DEFINIR LOS FORMULARIOS VACIOS Y CON VALORES PLS
##########################################################################################
class textoplano:

    def formulario(self,val):
        if val!=None:
            formulario = textoPlano(val)
        else:
            formulario = textoPlano()
        return formulario

class ProjectFile:
    def formulario(self,val):
        if val!=None:
            formulario = ProjectFileForm(val)
        else:
            formulario = ProjectFileForm()
        return formulario
        
class ScenariosWithKeyWord:

    def formulario(self,val):
        if val!=None:
            formulario = ScenariosWithKeyWords(val)
        else:
            formulario = ScenariosWithKeyWords()
        return formulario
class Scenario:
    def formulario(self,val):
        if val!=None:
            formulario = Scenarios(val)
        else:
            formulario = Scenarios()
        return formulario
class KnowledgeGraph:
    def formulario(self,val):
        if val!=None:
            formulario = KnowledgeGraphs(val)
        else:
            formulario = KnowledgeGraphs()
        return formulario
 
class Boton():
    def __init__(self,nom,clave):
        self.nombre=nom
        self.cod=clave

##################################EXTENCIONES DE HERRAMIENTRAS ###############################
#SE REQUIERE DE HACER LA CLASE PARA LA FUNCIONALIDAD Y AGREGAR EL BOTON EN 
#LA FUNCION listaBotones
#############################################################################################
def listaBotones():
    #se va a llamar en la view artefactos para generar los botones
    #aca se especifican las funcionalidades personalizadas
    #esto se hace para hacerlo mas dinamico
    #Tener en cuenta! es muy importante generar una clave,
    #al momento donde el usuario elije el boton de la funcionalidad N
    #se llamaran a todas las funcionalidades y la que tenga la clave correcta(o boton)
    #es la que se ejecutara
    #MUY IMPORTANTE CHEQUEAR POR LA CLAVE EN EL OBJETO DE LA FUNCIONALIDAD!
    botones=[]
    botones.append(Boton("Create a knowledge graph","kg"))
    botones.append(Boton("To UML","uml"))
    botones.append(Boton("Convert to ScenarioKeyWords","cskw"))
    botones.append(Boton("Export Scenario with keywords to txt file","exportSKW"))
    botones.append(Boton("Validate knowledge graph","shacl4j"))
    return botones
    
def funcionalidadesRegitradas(request,entidadesSeleccionadas,idP):
    #REGISTRE ACA SU FUNCIONALIDAD
    #paradigma por broadcast event based
    if KG.knowledgeGraph(entidadesSeleccionadas,request):
        return 'kg'
    if UML.funcionalidad(entidadesSeleccionadas,request,idP):
        return 'uml'
    if TransformarAScenariosKeyWords.funcionalidad(entidadesSeleccionadas,request,idP):
        return 'cskw'
    if ExportarEscenariosKeyWordsATxt.funcionalidad(entidadesSeleccionadas,request):
        return 'exportSKW'
    if SHACL4J.funcionalidad(entidadesSeleccionadas,request):
        return 'shacl4j'

class SHACL4J:
    def funcionalidad(sel,request):
        if "shacl4j" in request.GET:
            file= StringIO(Artefacto.objects.get(id=sel[0]).texto)
            response_report= requests.post("https://guarded-falls-24810.herokuapp.com/validate_ttl", files={"file": file})
            request.session["textoTxt"] = response_report.text
            return "OK"
        else:
            return None

class KG():
    def knowledgeGraph(sel,request):
        if 'kg' in request.GET:
            esce=[]
            for i in sel:
                if Artefacto.objects.get(id=i).tipoDeArtefacto.tipo=="Scenario":
                    esce.append(i)
            #print(esce)
            if esce:
                escenarios=formatoToKG(esce)
                data = json.loads(escenarios)
                Wikilink().enrich(Ontoscen(list(map(lambda req: Requirement(req), data)))).serialize("data/output.ttl", format="n3", encoding="utf-8")
                file=open("data/output.ttl", mode="r", encoding="utf-8")
                
                return "SI"
        else:
            return None
                

def formatoToKG(esce):
    """
    The input file must be a list of JSON objects with the following
    structure:
        {
            "scenario": <str>,
            "goal": <str>,
            "context": <str>,
            "actors": <list[str]>,
            "resources": <list[str]>,
            "episodes": <list[str]>
        }
    """
    textF="["
    for i in esce:
        art=Artefacto.objects.get(id=i)
        textF=textF+"{"
        textF=textF+'"scenario":'+'"'+art.nombre+'"'+","
        cont=json.loads(art.texto)
        textF=textF+'"goal":'+'"'+cont["Goal"]+'"'+","
        textF=textF+'"context":'+'"'+cont["Context"]+'"'+","
        textF=textF+'"actors":'+json.dumps(separarPorComa(cont["Actors"]))+","
        textF=textF+'"resources":'+json.dumps(separarPorComa(cont["Resources"]))+","
        textF=textF+'"episodes":'+json.dumps(separarPorPunto(cont["Episodes"]))
        textF=textF+"},"
    textF=textF.rstrip(textF[-1])
    textF=textF+"]"
    #print(json.loads(textF))
    return textF
def separarPorComa(actoresStr):
    lista=[]
    lista.extend(actoresStr.split(","))
    return lista
def separarPorPunto(actoresStr):
    lista=[]
    lista.extend(actoresStr.split("."))
    return lista

def buscarClase(arr,clase):

    for i in arr:
        #
        if (i["nombre"]==clase):
            #print("ENCONTRO")
            return i
    return None
def tranfSetArr(set):
    arr=[]
    for i in set:
        arr.append(i)
    return arr
class UML:
    def transformarTexto(texto):
        textoTransformado = texto
        return textoTransformado
    def separar_oraciones(texto):
            
        matcher = Matcher(nlp.vocab)
        pattern_one = [{'POS': 'CCONJ'}]
     
        matcher.add('separar_oraciones', [pattern_one])
        doc= nlp(texto)
        matches = matcher(doc)

        oraciones_separadas = []
        
        pos = 0
        for match_id, start, end in matches:
            frase = doc[pos : start].text
            pos = end
            oraciones_separadas.append(frase + '.')

        frase =doc[pos:].text
        oraciones_separadas.append(frase)
        sentence=""
        for oracion in oraciones_separadas: 
            sentence += oracion
        texto_procesado= [sentence]

        return texto_procesado
    @classmethod
    def identificarClases(self, texto):
        matcher = Matcher(nlp.vocab)
        pattern = [{"POS": "NOUN"}]
        matcher.add("Class Candidate", [pattern])
        pattern = [{"DEP": {"IN": ["nsubj", "dobj", "iobj"]}}]
        matcher.add("Class Candidate", [pattern])
        clasesIdentificadas = set()
        print("-----------------------------------------------")
        print(texto)
        texto = UML.break_into_sentences(texto)
        for o in texto:
            doc = nlp(o)
            matches = matcher(doc)
            for match_id, start, end in matches:
                matched_span = doc[start:end]
                clasesIdentificadas.add(matched_span.lemma_.lower())
        return clasesIdentificadas


    def break_into_sentences(parrafo):
        parrafo = parrafo.replace("\r", "¥")
        parrafo = parrafo.replace("\n", "¥")
        parrafo = parrafo.replace(". ", "¥")
        parrafo = " ".join(parrafo.split())
        parrafo += "¥"

        result = []
        pos_ini = 0
        pos = 0
        while pos < len(parrafo):
            c = parrafo[pos]
            if c != "¥":
                pos += 1
            else:
                result.append(parrafo[pos_ini:pos])
                while pos < len(parrafo) and not parrafo[pos].isalnum():
                    pos += 1
                pos_ini = pos
        return result

    def buscarClase(arr, clase):
        for elem in arr:
            if (elem["nombre"] == clase):
                return elem
        return None

    def identificarMetodosDeClase(self, clases, texto):
        verbosProhibidos = ["contener", "ser", "es", "tener"]
        metodosDeClaseIdentificados = []
        texto = UML.break_into_sentences(texto)
        for o in texto:
            doc = nlp(o)
            for classToken in doc:
                if (classToken.dep_ == "obj") & (classToken.lemma_.lower() in clases):
                    claseLeida = classToken.lemma_.lower()
                    for verbToken in doc:
                        if (verbToken.pos_ == "VERB") & (verbToken.lemma_ not in verbosProhibidos):
                            repetido = buscarClase(metodosDeClaseIdentificados, claseLeida)
                            if (repetido == None):
                                aux = {
                                    "nombre" : claseLeida,
                                    "metodos" : [verbToken.lemma_]
                                }
                                metodosDeClaseIdentificados.append(aux)
                            else:
                                if (verbToken.lemma_ not in repetido["metodos"]):
                                    repetido["metodos"].append(verbToken.lemma_)
        return metodosDeClaseIdentificados

    def identificarRelaciones(self,clases,texto):

        # evalua si la entidad(sustativo) existe
        def buscarSiYaExiste(sustantivo, relacionesIdentificados):
            for palabra in relacionesIdentificados:
                if palabra["nombre"] == sustantivo:
                    return True
            return False

        # retorna true si ya existe la relacion
        def existeRelacion(palabra, relacionesIdentificadas):
            for entidad in relacionesIdentificadas:
                if palabra in entidad["relacion"] or palabra in entidad["subclase"]:
                    return True
            return False

        # agrega la relacion al sust
        def evaluarPalabra(sustantivo, sustantivoRelacion, relaciones, esHerencia):
        # verifico que las realciones o sublcases no se repitan, sino creo o sumo una nueva entidad/relacion
            if not existeRelacion(sustantivoRelacion, relaciones):
                if not (buscarSiYaExiste(sustantivo, relaciones)):
                    palabra = {
                        "nombre": sustantivo,
                        "relacion": [],
                        "subclase": []
                    }
                    relaciones.append(palabra)
                # itero en relaciones hasta encontrar la entidad de sustativo
                for palabra in relaciones:
                    if palabra["nombre"] == sustantivo:
                        if esHerencia:
                            palabra["subclase"].append(sustantivoRelacion)
                        else:
                            palabra["relacion"].append(sustantivoRelacion)

        pattern_one = [{'TEXT': {"IN": clases}}, {"OP": "?"}, {"OP": "?"},
                       {'POS': {'IN': ['VERB', 'AUX']}}, {"OP": "?"}, {"OP": "?"},
                       {'TEXT': {"IN": clases}}]
        matcher = Matcher(nlp.vocab)
        matcher.add('relaciones', [pattern_one])

        relacionesIdentificadas = []
        for o in texto:
            doc = nlp(o)
            texto_2 = "".join([token.lemma_ + " " for token in doc])
            doc2 = nlp(texto_2)
            matches = matcher(doc2)
            # itero por cada match encotrado
            for match_id, start, end in matches:
                frase = doc2[start: end]
                sustantivo = []
                # itero en la frase del doc para obtener los sust y el verb
                for tok in frase:
                    if tok.text in clases:
                        sustantivo.append(tok.text)
                    elif tok.pos_ == "VERB" or tok.pos_ == "AUX":
                        verb = tok.text
                if (sustantivo[0], sustantivo[1] in clases):
                    # verifico que los sust sean clases ya identificadas
                    if not existeRelacion(sustantivo[0], relacionesIdentificadas):
                        if verb == "ser":
                            evaluarPalabra(sustantivo[1], sustantivo[0], relacionesIdentificadas, True)
                        else:
                            evaluarPalabra(sustantivo[0], sustantivo[1], relacionesIdentificadas, False)

        return relacionesIdentificadas

    def eliminar_tildes(self,texto: str) -> str:
        import unidecode
        return unidecode.unidecode(texto.lower())
    @classmethod
    def funcionalidad(self,sel,request,idP):

        if 'uml' in request.GET:
            textosId=[]
            for i in sel:
                if Artefacto.objects.get(id=i).tipoDeArtefacto.tipo=="textoplano":
                    textosId.append(i)
        else:
            return None
        texto=[]
        
        for i in textosId:
            art=Artefacto.objects.get(id=i)
            texto.append(json.loads(art.texto)["texto"])

        
        #texto es un arreglo con los textos que vienen seleccionados

        if not texto:
            return None
        merge=""
        for i in texto:
            merge= merge + i + " "
        texto[0]=merge
        aux_2=UML.separar_oraciones(texto[0])
        texto=aux_2
        aux=[]
        for i in texto:
            aux.append(self.eliminar_tildes(self,i))
        texto=aux
        clases=tranfSetArr(UML.identificarClases(texto[0]))
        metodos=UML.identificarMetodosDeClase(self,clases,texto[0])
        relaciones=UML.identificarRelaciones(self,clases,texto)
        data=[]
        #expression_if_true if condition else expression_if_false
        for clase in clases:
            z=buscarClase(relaciones,clase)
            x=buscarClase(metodos,clase)
            #print(buscarClase(metodos,clase))
            c={
                "nombre" : clase,
                "metodos":x["metodos"] if x!=None else [],
                "subclases":z["subclase"] if z!=None else [],
                "atributos":[],
                "relaciones":z["relacion"] if z!=None else []
                }
            x=[]
            z=[]
            data.append(c)
        #data es lo que devolveria luego del procesamiento
        #print(data)
        request.session["UMLDATA"] = data
        return "OK"
 #diccionario= obj clase
 # data = [
 #       {
  #          "nombre": "empresa",
  #          "atributos": ["travesia", "calle", "numero", "codigoPostal", "ciudad", "provincia", "pais"],
  #          "relaciones": ["cliente", "proveedor", "empleado"],
  #          "metodos": ["ofrecer", "pedir", "pagar", "pagar_servicio"],
  #          "subclases": ["empresa_publica", "empresa_privada"],
  #      },
  #      {
  #          "nombre": "empresa_publica",
  #          "atributos": ["travesia"],
  #          "relaciones": [],
   #         "metodos": ["ofrecer"],
   #         "subclases": [],
   #     },
   # ]

class TransformarAScenariosKeyWords:
    #CONVIERTE UN ESCENARIO NORMAL A UNO CON KEYWORDS
    def desarreglar(arr):
        ea=""
        for i in arr:
            ea =ea+i+" "
        return ea
    def get_string_episode_keywords(episodes):
        resultado = ""
        for episode in episodes:
            resultado += (episode["subject"][0] + ", ") if len(episode["subject"]) > 0 else ""
            resultado += (episode["verb"][0] + ", ") if len(episode["verb"]) > 0 else ""
            resultado += (episode["object"][0]) if len(episode["object"]) > 0 else ""
            resultado += "\n"
        return resultado
    def funcionalidad(sel,request,idP):
        if 'cskw' in request.GET:
            esce=[]
            for i in sel:
                if Artefacto.objects.get(id=i).tipoDeArtefacto.tipo=="Scenario":
                    esce.append(i)
            #print(esce)
            for i in esce:
                TransformarAScenariosKeyWords.convertidor(Artefacto.objects.get(id=i),request,idP)
            return "OK"
        else:
            return None
    def get_scenario_with_keywords(data):
        NLP = spacy.load("en_core_web_trf")

        def get_formatted_keywords(list):
            if len(list) == 0:
                return ""
            return ", ".join(list) if len(list) > 1 else list[0]

        try:
            nombreKeyWords = [token.text for token in NLP(data["nombre"]) if token.pos_ == "VERB"]
            GoalKeyWords = [token.text for token in NLP(data["Goal"]) if token.pos_ == "VERB"]
            ContextKeyWords = [token.text for token in NLP(data["Context"]) if token.pos_ == "NOUN"]
            ResourcesKeyWords = [token.text for token in NLP(data["Resources"]) if token.pos_ == "NOUN"]
            ActorsKeyWords = [token.text for token in NLP(data["Actors"]) if token.pos_ == "NOUN"]
            EpisodesKeyWords = [{
                "subject": [token.text for token in NLP(episode) if token.dep_ == "nsubj"],
                "verb": [token.text for token in NLP(episode) if token.pos_ == "VERB"],
                "object": [token.text for token in NLP(episode) if token.dep_ == "dobj"]
            } for episode in data["Episodes"]]

            scenario_with_keywords = {
                "nombre": data["nombre"],
                "nombreKeyWords": nombreKeyWords[0] if len(nombreKeyWords) > 0 else "",
                "Goal": data["Goal"],
                "GoalKeyWords": GoalKeyWords[0] if len(GoalKeyWords) > 0 else "",
                "Context": data["Context"],
                "ContextKeyWords": ContextKeyWords[0] if len(ContextKeyWords) > 0 else "",
                "Resources": data["Resources"],
                "ResourcesKeyWords": get_formatted_keywords(ResourcesKeyWords),
                "Actors": data["Actors"],
                "ActorsKeyWords": get_formatted_keywords(ActorsKeyWords),
                "Episodes": data["Episodes"],
                "EpisodesKeyWords": EpisodesKeyWords
            }
            return scenario_with_keywords
        except Exception as e:
            print(e)
            return {}
    def adaptarListaDeElementosPlanoAArreglo(esc):
        ep=""
        arreglo=[]
        for i in esc:
            
            if i == ".":
                arreglo.append(ep)
                ep=""
            else:
                ep+=i
        arreglo.append(ep)
        return arreglo

    def convertidor(escenario,request,idP):
        cont=json.loads(escenario.texto)
        escenarioAdaptado={
            "nombre":cont["nombre"],
            "Goal":cont["Goal"],
            "Context":cont["Context"],
            "Resources":cont["Resources"],
            "Actors":cont["Actors"],
            "Episodes":TransformarAScenariosKeyWords.adaptarListaDeElementosPlanoAArreglo(cont["Episodes"]),
        }
        #print(TransformarAScenariosKeyWords.adaptarListaDeElementosPlanoAArreglo(cont["Episodes"]))
        #print(escenarioAdaptado)
        escKW=TransformarAScenariosKeyWords.get_scenario_with_keywords(escenarioAdaptado)
        escKW["ResourcesKeyWords"]=escKW["ResourcesKeyWords"]
        escKW["ActorsKeyWords"]=escKW["ActorsKeyWords"]
        cosas=escKW["EpisodesKeyWords"]
        escKW["EpisodesKeyWords"]=TransformarAScenariosKeyWords.get_string_episode_keywords(cosas)
        aux=TransformarAScenariosKeyWords.desarreglar(escKW["Episodes"])
        escKW["Episodes"]=aux
        #print("ESCENARIO")
        #print(escKW)
        nuev=Artefacto(owner=request.user,nombre=escenario.nombre,tipoDeArtefacto=TipoDeArtefacto.objects.get(tipo="ScenariosWithKeyWord"),texto=json.dumps(escKW))
        nuev.save()
        p= Proyecto.objects.get(id=idP)
        p.artefactos.add(nuev)
        p.save()
class ExportarEscenariosKeyWordsATxt:
    def linea(escenario):
        #recibo escenanario y lo convierto en una linea
        nombre=escenario.nombre
        contenido=json.loads(escenario.texto)
        separador=";"
        line=""+"Escenario: "+nombre+separador
        line=line+" "+"GoalKeWords: "+contenido["GoalKeyWords"]+separador
        line=line+" "+"ContextKeyWords: "+contenido["ContextKeyWords"]+separador
        line=line+" "+"ResourcesKeyWords: "+contenido["ResourcesKeyWords"]+separador
        line=line+" "+"ActorsKeyWords: "+contenido["ActorsKeyWords"]+separador
        line=line+" "+"EpisodesKeyWords: "+contenido["EpisodesKeyWords"]+separador
        line=line+"\n"#salto de pagina
        return line
    def funcionalidad(sel,request):
        texto=""
        if 'exportSKW' in request.GET:
            for i in sel:
                esc=Artefacto.objects.get(id=i)
                if esc.tipoDeArtefacto.tipo=="ScenariosWithKeyWord":
                    texto=texto+ExportarEscenariosKeyWordsATxt.linea(esc)
            #print(texto)
            request.session["textoTxt"] = texto
            #response = HttpResponse(content_type='text/plain')  
            #response['Content-Disposition'] = 'attachment; filename="keyWordsDeLosEscenarios.txt"'
            #response.write('Hello')
            return "OK"
##########################################################################################################
#
# IA - EXPERIMENTAL - Extraccion de entidades
#
#~#######################################################################################################
def pantallaDePruebas(request):
    listado = request.GET.getlist('seleccionados')
    if request.method == "POST":
        formulario = Entidades(request.POST)
        if formulario.is_valid():
            texto = formulario.cleaned_data["texto"]
            url = "http://127.0.0.1:8000/ia/"
            data ={
                "nombre": "Funcionalidad de prueba de IA",
                "texto": texto
            }

            post_response = requests.post(url, json=data)
            post_response_json = post_response.json()
            #print(post_response_json)
            listado = post_response_json


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
        from app.settings import BASE_DIR
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
            from app.settings import BASE_DIR
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
def prepararData():
    from app.settings import BASE_DIR
    from spacy.tokens import DocBin
    #import json
    archivo = open(os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','Datos','datasetUsuario.json'), encoding='utf-8').read()
    TRAIN_DATA  = json.loads(archivo)
#print(TRAIN_DATA)
#FALTA DATOS INNCORRECTOS
    nlp = spacy.load(os.path.join(os.path.dirname(BASE_DIR), 'app', 'output/model-best'))
    db = DocBin()
    i=1
    for text, annotations in TRAIN_DATA:
        doc = nlp(text)
        ents = []
        i+=1
        for start, end, label in annotations:
            span = doc.char_span(start, end, label=label)
            if span == None:
                print(text)
            print(span,i)
            ents.append(span)
        doc.ents = ents
        db.add(doc)
    db.to_disk("app/ConfigTraining/Datos/trainUser.spacy")
def pantallaTraining(request):
    import subprocess
    from app.settings import BASE_DIR
    prepararData()
    subprocess.run(["python","-m","spacy","train",os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','config.cfg'),"--output","./output","--paths.train",os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','Datos','trainUser.spacy'),'--paths.dev',os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','Datos','trainPlantas.spacy')])
    return render(request,'IA/consolaTraining.html',{"ok":False})
def pantallaDeIA(request):
    return render(request,'IA/pantallaDeTraining.html',{})
##########################################################################################################
#
# IA - EXPERIMENTAL - TOPICOS - 
#
#~#######################################################################################################
def clean(doc,stop,exclude,lemma):
    #limpieza de palabras o caracteres que no suman informacion
    stop_free = " ".join([i for i in doc.lower().split()if i not in stop])
    punc_free = "".join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    return normalized
def format_topics_sentences(ldamodel,corpus):
    # Init output
    sent_topics_df = pd.DataFrame()

    # Get main topic in each document
    for i, row in enumerate(ldamodel[corpus]):
        row = sorted(row, key=lambda x: (x[1]), reverse=True)
        # Get the Dominant topic, Perc Contribution and Keywords for each document
        for j, (topic_num, prop_topic) in enumerate(row):
            if j == 0:  # => dominant topic
                wp = ldamodel.show_topic(topic_num)
                topic_keywords = ", ".join([word for word, prop in wp])
                sent_topics_df = sent_topics_df.append(pd.Series([int(topic_num), round(prop_topic,4), topic_keywords]), ignore_index=True)
            else:
                break
    sent_topics_df.columns = ['Dominant_Topic', 'Perc_Contribution', 'Topic_Keywords']
    return sent_topics_df

def identificarTopicos(doc_complete) :
    stop = set(stopwords.words('english'))
    exclude = set(string.punctuation)
    lemma = WordNetLemmatizer()
    doc_clean = [clean(doc,stop,exclude,lemma).split() for doc in doc_complete]
    #preprocesamiento terminado
    #creo un diccionario de terminos unicos (no se repten)
    dictionary = corpora.Dictionary(doc_clean)
    #convierto la lista en una matrix doc - termino
    doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]
    # Creating the object for LDA model using gensim library
    Lda = gensim.models.ldamodel.LdaModel
    # Running and Training LDA model on the document term matrix
    #for 3 topics.
    ldamodel = Lda(doc_term_matrix, num_topics=3, id2word =
    dictionary, passes=50)
    # Results
    #print(ldamodel.print_topics())
    topicos = ldamodel.show_topics(formatted=False)
    print(topicos[0][1])
    #topicos_ordenados = topicos[0][1].sort(key=lambda a: a[1],reverse=True)
    #print(topicos_ordenados)
    result = format_topics_sentences(ldamodel,doc_term_matrix)
    #print(result)
    #print(result['Topic_Keywords'][0])
    return result
def separarEnLineas(texto):
    #se usa en desambiguar tb
    arr = []
    oracion = ""
    for i in texto:
        oracion += i
        if i ==".":
            arr.append(oracion)
            oracion = ""
    return arr
def preparar_texto(seleccionados):
    artef = []
    textos = []
    for i in seleccionados:
        artef.append(Artefacto.objects.get(id = i))
    for i in artef:
        texto= json.loads(i.texto)
        textos.append(texto["texto"])
    arreglo_texto_Oracion = []
    for i in textos:
        arreglo_texto_Oracion.append(separarEnLineas(i))
    #print(arreglo_texto_Oracion)
    resultados = []
    for i in arreglo_texto_Oracion:
        rusul = identificarTopicos(i)
        resultados.append(rusul)
    return resultados
    
        

def pruebaAlgoritmoTopic(request) :
    topicos = False
    if request.method == "GET":
        seleccionados = request.GET.getlist('seleccionados')
        resul = preparar_texto(seleccionados)
        #print(resul)
        re_topico = []
        l = 0
        for j in resul:
            re_topico.append((j["Topic_Keywords"][0],seleccionados[l]))
            l += 1
        #print(re_topico)
        topicos = True
    artefactos = Artefacto.objects.all()
    usuario=request.user
    ok = False
    artefactos_usuario = []
    for p in artefactos:
        if p.owner==usuario:
            u = {
                "titulo" : p.nombre,
                 "tipoDeArtefacto": p.tipoDeArtefacto,
                 "topic" : None,
                 "id" : p.id
                }
            artefactos_usuario.append(p)
            ok=True
    if topicos:
        for i in artefactos_usuario:
            for j in re_topico:
                if str(i.id) == str(j[1]):
                    i.topic = j[0]
    return render(request,'IA/clasificador.html',{"ok":ok,"artifacts":artefactos_usuario,"topicos":topicos})
##########################################################################################################
#
# IA - EXPERIMENTAL - Desambiguar 
#
#~#######################################################################################################
def prepararDatosParaDesambiguar(texto):
    result = separarEnLineas(texto)
    return result
def desambiguacion(request):
    from nltk.corpus import wordnet as wn
    from nltk.stem import PorterStemmer
    from itertools import chain
    from pywsd.lesk import simple_lesk
    # Sentences
    #bank_sents = ['I went to the bank to deposit my money',
    #'The river bank was full of dead fishes']
    # calling the lesk function and printing results for both the 
    # sentences
    #print ("Context-1:", bank_sents[0])
    #answer = simple_lesk(bank_sents[0],'bank')
    #print ("Sense:", answer)
    #print ("Definition : ", answer.definition())
    #print ("Context-2:", bank_sents[1])
    #answer = simple_lesk(bank_sents[1],'bank','n')
    #print ("Sense:", answer)
    #print ("Definition : ", answer.definition())
    mostrar=[]
    if request.method == "POST":
        formulario = Entidades(request.POST)
        mostrar = []
        if formulario.is_valid():
            data = formulario.cleaned_data["texto"]
            datos = json.loads(data)
            oraciones = separarEnLineas(datos[0])
            seleccion = datos[1]
            respuesta = []
            datass={"texto": datos[0]}
            formulario=Entidades(datass,initial=datass)
            for i in oraciones:
                for j in seleccion:
                    if j in i:
                        answer = simple_lesk(i,j)
                        respuesta.append(answer)
            
            for i in respuesta:
                #print(i.definition())
                mostrar.append(i.definition())
    else:
        formulario = Entidades()
    return render(request,'IA/pantallaDeDesambiguar.html',{"form" : formulario,"def":mostrar})
##########################################################################################################
#
# IA - EXPERIMENTAL - Clustering 
#
#~#######################################################################################################
def tokenize_and_stem(text):
    import nltk
    from nltk.stem.snowball import SnowballStemmer
    stemmer = SnowballStemmer("english")
    tokens = [word for sent in nltk.sent_tokenize(text) for
    word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems
def tokenize_only(text):
    import nltk
    tokens = [word.lower() for sent in nltk.sent_tokenize(text)
    for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    return filtered_tokens
def clustering(request):
    import numpy as np
    import pandas as pd
    import nltk
    
    from bs4 import BeautifulSoup
    import re
    import os
    import codecs
    from sklearn import feature_extraction
    import mpld3
    from sklearn.metrics.pairwise import cosine_similarity
    import os
    from sklearn.manifold import MDS
    artefactos = Artefacto.objects.all()
    textos = []
    usuario=request.user
    texto_art=[]
    for i in artefactos:
        if i.owner == usuario and i.tipoDeArtefacto.tipo=="textoplano":
            texto_art.append(i)
            textos.append(json.loads(i.texto)["texto"])
    ranks = []
    for i in range(1, len(textos)+1):
        ranks.append(i)
    # Stop Words
    otro = ["'d", "'s", 'abov', 'ani', 'becaus', 'befor', 'could', 'doe', 'dure', 'might', 'must', "n't", 'need', 'onc', 'onli', 'ourselv', 'sha', 'themselv', 'veri', 'whi', 'wo', 'would', 'yourselv','used','also'] 
    stopwords = nltk.corpus.stopwords.words('english') + otro
    
    # Load 'stemmer'
    
    from sklearn.feature_extraction.text import TfidfVectorizer
# tfidf vectorizer
    tfidf_vectorizer = TfidfVectorizer(max_df=0.8, max_features=200000,min_df=0.2, stop_words=stopwords,
    use_idf=True, tokenizer=tokenize_and_stem, ngram_range=(1,3))
    #fit the vectorizer to data
    tfidf_matrix = tfidf_vectorizer.fit_transform(textos)
    terms = tfidf_vectorizer.get_feature_names_out()
    #print(tfidf_matrix.shape)
    #Import Kmeans
    from sklearn.cluster import KMeans
    # Define number of clusters
    num_clusters = 6
    #Running clustering algorithm
    km = KMeans(n_clusters=num_clusters)
    km.fit(tfidf_matrix)
    #final clusters
    clusters = km.labels_.tolist()
    complaints_data = { 'rank': ranks, 'complaints': textos,
    'cluster': clusters }
    frame = pd.DataFrame(complaints_data, index = [clusters,ranks] ,
    columns = ['rank', 'cluster'])
    #number of docs per cluster
    #print(frame['cluster'].value_counts())
    totalvocab_stemmed = []
    totalvocab_tokenized = []
    for i in textos:
        allwords_stemmed = tokenize_and_stem(i)
        totalvocab_stemmed.extend(allwords_stemmed)
        allwords_tokenized = tokenize_only(i)
        totalvocab_tokenized.extend(allwords_tokenized)
    vocab_frame = pd.DataFrame({'words': totalvocab_tokenized}, index = totalvocab_stemmed)
    #sort cluster centers by proximity to centroid
    clusterEncontrados=""
    clasificacion = []
    order_centroids = km.cluster_centers_.argsort()[:, ::-1]
    for i in range(num_clusters):
        clusterEncontrados+= "Cluster "+str(i)+". Clasificado por: "
        print("Cluster %d words:" % i, end='')
        for ind in order_centroids[i, :6]:
            print(' %s' % vocab_frame.loc[terms[ind].split(' ')].
            values.tolist()[0][0].encode('utf-8', 'ignore'), end=',')
            clusterEncontrados+=str(vocab_frame.loc[terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8', 'ignore'))+", "
        print('\n')
        clasificacion.append(clusterEncontrados)
        clusterEncontrados = ""
    #print(frame)
    artef = []
    for i in frame.index:
        artef.append((i[0],texto_art[i[1]-1]))
    #print(artef)
    ordenado = sorted(artef, key=lambda a: a[0])
    #print(ordenado)
    return render(request,'IA/Clustering.html',{"cluster":clasificacion,"arte":ordenado})

##########################################################################################################
#
# IA - EXPERIMENTAL - Similaridad
#0
#~#######################################################################################################
def simility(request):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    respuesta = None
    if request.method == "GET":
        seleccionados = request.GET.getlist('seleccionados')
        #print(seleccionados)
        if len(seleccionados) > 1:
            documents = [json.loads(Artefacto.objects.get(id = seleccionados[0]).texto)['texto'],json.loads(Artefacto.objects.get(id = seleccionados[1]).texto)['texto']]
            #print(documents)
            tfidf_vectorizer = TfidfVectorizer()
            tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
            resultados = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)
            #print(resultados[0][1])
            respuesta = "Simility: "+ str(resultados[0][1])

    artefactos = Artefacto.objects.all()
    usuario=request.user
    ok = False
    artefactos_usuario = []
    for p in artefactos:
        if p.owner==usuario:
            u = {
                "titulo" : p.nombre,
                 "tipoDeArtefacto": p.tipoDeArtefacto,
                 "id" : p.id
                }
            artefactos_usuario.append(p)
            ok=True
    
    #documents = (
    #"I like NLP",
    #"I am exploring NLP",
    #"I am a beginner in NLP",
    #"I want to learn NLP",
    #"I like advanced NLP"
    #)
    #tfidf_vectorizer = TfidfVectorizer()
    #tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
    #print(tfidf_matrix.shape)
    #resultados = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)
    #print(resultados[0])
    return render(request,'IA/similaridad.html',{"ok":ok,"artifacts":artefactos_usuario,"resp":respuesta})
##########################################################################################################
#
# IA - EXPERIMENTAL - Resumen
#0
#~#######################################################################################################
def resumen(request):
    from sumy.parsers.html import HtmlParser
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lsa import LsaSummarizer
    from sumy.nlp.stemmers import Stemmer
    from sumy.utils import get_stop_words
    from sumy.summarizers.luhn import LuhnSummarizer
    # Extracting and summarizing
    resum = None
    #for sentence in summarizer(parser.document, SENTENCES_COUNT):
        #print(sentence)
    if request.method == "POST":
        formulario = UrlForm(request.POST)
        if formulario.is_valid():
            #print(formulario.cleaned_data["url"])
            url = formulario.cleaned_data["url"]
            LANGUAGE = "english"
            SENTENCES_COUNT = 10
            #url="https://en.wikipedia.org/wiki/Natural_language_processing"
            parser = HtmlParser.from_url(url, Tokenizer(LANGUAGE))
            summarizer = LsaSummarizer()
            summarizer = LsaSummarizer(Stemmer(LANGUAGE))
            summarizer.stop_words = get_stop_words(LANGUAGE)
            formulario=None
            resum= summarizer(parser.document, SENTENCES_COUNT)
        formulario = UrlForm()
    else:
        formulario = UrlForm()
    return render(request,'IA/resumen.html',{"form":formulario,"resumen":resum})
##########################################################################################################
#
# Similaridad de escenarios
#0
#~#######################################################################################################
def algunSinonimoMatchea(listaOriginal,lista):
    for sin in lista:
        for word in listaOriginal:
            if word == sin:
                #print("Encontro match", sin)
                return sin
    return None
def sinonimos(lista1,lista2):
    from nltk.corpus import wordnet 
    li1 = lista1.split()
    li2 = lista2.split()
    #print("lista del escenario seleccionado ",li1)
    print("antes : ",li2)
    cambio = set()
    for i in li2:
        for sin in wordnet.synsets(i):
            #print("-------------PALABERAAA-------------")
            #print(i)
            #print(sin.lemma_names())
            #aca esta el tema sin.lemma_names() es una lista debo programar algo para identificar!
            
            palabrita = algunSinonimoMatchea(li1,sin.lemma_names())
            #print(palabrita)
            if palabrita != None:
                #print(i, " es sinonimo de  ",palabrita)
                i = palabrita
                cambio.add(palabrita)
            else:
                if i not in cambio:
                    cambio.add(i)
    res= ""
    print("despues : ",cambio)
    for i in li2:
        res= res + i + " "
    return res
def compararEpisodeos(esc_a,esc_b,nlp):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    nlp = spacy.load('en_core_web_trf')
    doc_a = nlp(esc_a)
    doc_b = nlp(esc_b)
    verbos_a = ''
    verbos_b = ''
    for token in doc_a:
        if token.pos_ == "VERB":
            verbos_a= verbos_a + token.lemma_ + " "
    for token in doc_b:
        if token.pos_ == "VERB":
            verbos_b= verbos_b + token.lemma_ + " "
    print("LISTA DE VERBOS!")
    print(verbos_a)
    print(verbos_b)
    resultado = compararRecursosYActores(verbos_a,verbos_b)
    return resultado
def compararRecursosYActores(lista1,lista2):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    documents = [lista1,sinonimos(lista1,lista2)]
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
    resultados = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)
    return resultados[0][1]
def compararFields(context1,context2):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    documents = [context1,context2]
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
    resultados = cosine_similarity(tfidf_matrix[0:1],tfidf_matrix)
    return resultados[0][1]
def scenarioSimilarity(escenario,escenariosDelUsuario):
    #comparo actores
    #comparo recursos
    print(escenario)
    nlp = spacy.load('en_core_web_trf')
    for escUser in escenariosDelUsuario:
        esc_a = json.loads(escUser.texto)
        stop = set(stopwords.words('english'))
        exclude = set(string.punctuation)
        lemma = WordNetLemmatizer()
        recursos_actores_esc1=clean(escenario['Resources']+" "+escenario['Actors'],stop,exclude,lemma)
        recursos_actores_esc2=clean(esc_a['Resources']+" "+esc_a['Actors'],stop,exclude,lemma)
        goal_esc1 = clean(escenario['Goal'],stop,exclude,lemma)
        goal_esca = clean(esc_a['Goal'],stop,exclude,lemma)
        resultados_contexto = compararFields(goal_esc1,goal_esca)
        resultados_episodeos = compararEpisodeos(escenario['Episodes'],esc_a['Episodes'],nlp)
        #print(lista1)
        resultados_actores_escenarios= compararRecursosYActores(recursos_actores_esc1,recursos_actores_esc2)
        print("Actores y recursos, similaridad: "+esc_a['nombre'],resultados_actores_escenarios)
        print("Objetivo, similaridad: "+esc_a['nombre'],resultados_contexto)
        print("Episodeos, similaridad: ",resultados_episodeos)
        print("Promedio: ",(resultados_contexto + resultados_actores_escenarios+ resultados_episodeos)/3)
    # respuesta = "Simility: "+ str(resultados[0][1])
def compararEscenario(request):
    artefactos = Artefacto.objects.all()
    usuario=request.user
    #Filtro los escenarios / escenarios con keywords del usuario
    escenariosDelUsuario=[]
    for i in artefactos:
        if i.owner == usuario and (i.tipoDeArtefacto.tipo == "Scenario" or i.tipoDeArtefacto.tipo == "ScenariosWithKeyWord"):
            escenariosDelUsuario.append(i)
    if request.method == "GET":
        seleccionados = request.GET.getlist('seleccionados')
        print(seleccionados)
        if len(seleccionados) >= 1:
            id = seleccionados[0]
            escenario = Artefacto.objects.get(id = id)
            scenarioSimilarity(json.loads(escenario.texto),escenariosDelUsuario)
    if escenariosDelUsuario:
        ok = True
    return render(request,'IA/similaridad.html',{"ok":ok,"artifacts":escenariosDelUsuario})


##########################################################################################################
#
# API TEST
#0
#~#######################################################################################################

class ArtefactosViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Artefacto.objects.all()
    serializer_class = ArtefactoSerializer
