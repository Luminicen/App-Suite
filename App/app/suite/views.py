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
from suite.ontoscen.analyzer import Analyzer
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

from spacy.matcher import DependencyMatcher
nlp_spanish = spacy.load("es_dep_news_trf")

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
############################### Api URL ##########################################
# Url de los modulos
####################################################################################
moduloneria = "http://moduloneria-requirements-healer.okd.lifia.info.unlp.edu.ar"

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
    similaritySC = ""
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
            #return redirect(reverse('ngram',kwargs={'idP':id}))
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
        elif funcionalidad=="ScSimil":
            similaritySC = request.session["similaridad_scenarios"]
        elif funcionalidad=="lelDT":
            return redirect(reverse('crearUML',kwargs={'idP':id}))
            #print("ACAAAAAA, ",similaritySC)
    botones=listaBotones()
    return render(request,'artefactos-lista.html',{"artifacts":escen,"ok":ok,"form":form,"formB":form2,"idP":id,"botones":botones,"similaridad":similaritySC})
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

def is_semantic_similar(text1, text2):
    return Analyzer().are_sentences_equivalent(text1, text2)

def process_episode(episode, scenarios):
    tree = { "name": episode, "children": [] }
    for scenario in scenarios:
        scenario = json.loads(scenario.texto)
        if is_semantic_similar(scenario["nombre"], episode):
            for sub_episode in scenario["Episodes"].split("\r\n"):
                tree["children"].append(process_episode(sub_episode, scenarios))
    return tree

def arbolEpisodios(request, id, idP):
    proyecto = Proyecto.objects.get(id=idP)
    scenarios = proyecto.artefactos.all().filter(tipoDeArtefacto__tipo="Scenario")
    artefacto = Artefacto.objects.get(id=id)
    if not tienePermiso(request.user, proyecto):
        return render(request,'ERRORES/403.html',{})
    texto = json.loads(artefacto.texto)
    episodes = texto["Episodes"].split("\r\n")
    tree = {
        "name": artefacto.nombre,
        "children": [process_episode(episode, scenarios) for episode in episodes]
    }
    return render(request, "proyecto-arbol.html", {"id": id, "idP": idP, "scenario": json.dumps(tree)})

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
    from app.settings import BASE_DIR
    
    context = {}
    try:
        static_url =  os.path.join(BASE_DIR,"app","static")
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
        import subprocess
        archivo = f"uml_{idP}.txt"
        #print(os.path.join(static_url,"plantuml.jar"))
        #print(os.path.join(static_url,"uml",archivo))
        #print(static_url)
        #os.system("dir "+ static_url)
        #subprocess.run("java","-jar", os.path.join(static_url,"plantuml.jar",os.path.join(static_url,"uml",archivo)) )
        #os.system("java -jar"+" "+ os.path.join(static_url,"plantuml.jar")+" "+ os.path.join(static_url,"uml",archivo))

    except Exception as e:
        context["error"] = str(e)
        print(e)
    subprocess.run(["java","-jar", os.path.join(static_url,"plantuml.jar"),os.path.join(static_url,"uml",archivo)])
    
    context["img_name"] = f"uml_{idP}.png"
    #request.session["LELCOMENTARIOS"] = comentarios
    if "LELCOMENTARIOS" in request.session:
        context["comentarios"] = request.session["LELCOMENTARIOS"]
    return render(request, 'uml-visualizer.html', context=context)
def detectar_ngramas(lista):

    def armar_estructura(doc, matches):
        lista_final = [];
        lista_aux = [];
        #guardo en la lista todas las palabras encontradas por el matcher
        #tengo que volver a poner esto con las prop de un token
        lista_matcheada = set([doc[start:end].text for match_id, start, end in matches])
        for token in doc:
            if(token.text in lista_matcheada) and (token.pos_ == 'NOUN') and (not token.text in lista_aux):
                palabra_base = token.text
                lista_asociados = list(filter(lambda a : palabra_base in a ,lista_matcheada))
                lista_aux.append(palabra_base) 
                lista_final.append((palabra_base, lista_asociados))
        return lista_final;

    pattern_esp_1 = [
            {'POS' : {'IN' : ['ADP', 'DET', 'PRON']}, 'OP' : '?'},
            {'POS' : {'IN' : ['NOUN', 'ADJ']}}, 
            {'POS' : {'IN' : ['ADP', 'DET', 'PRON']}, 'OP' : '?'},
            {'POS' : {'IN' : ['ADP', 'DET', 'PRON']}, 'OP' : '?'},
            {'POS' : {'IN' : ['NOUN', 'ADJ', 'PROPN']}}, 
            {'POS' : {'IN' : ['ADP', 'DET', 'PRON']}, 'OP' : '?'},
            {'POS' : {'IN' : ['NOUN', 'ADJ']}, 'OP' : '?'}, 
            {'POS' : {'IN' : ['ADP', 'DET', 'PRON','PROPN']}, 'OP' : '?'},
            {'POS' : {'IN' : ['NOUN', 'ADJ']}, 'OP' : '?'}, 
            {'POS' : {'IN' : ['ADP', 'DET', 'PRON','PROPN']}, 'OP' : '?'},
            ];

    pattern_esp_2 = [
            {'POS' : {'IN' : ['NOUN', 'ADJ']}}, 
            {'POS' : {'IN' : ['NOUN', 'ADJ', 'PROPN']}, 'OP' : '?'}, 
            ];

    matcher = Matcher(nlp.vocab)
    matcher.add("bigramas", [pattern_esp_1, pattern_esp_2])
    
    lista2= "".join(lista)
    doc = nlp(lista2)
    matches = matcher(doc)

    estrucutra_final = armar_estructura(doc, matches);

    """
        Detecta ngramas y devuelve un arreglo de ngramas 
        con referencia a alguna clase para poder reemplazar.
        formato de lista/diccionario:
        {'nombre': nombre_clase,
         'metodos': metodos_clase,
         'relaciones': relacion_entre_clases }
         output: los ngramas de la siguiente forma:
         arreglo: ('clase_detectada_de_lista', [lista de ngramas asociados])
    
    return [('cuenta',['cuenta bancaria','cuenta en','cuenta la','la cuenta']),('transferencia',['transferencia bancaria','tranferencia en la','transferencia x']),('deposito',['deposito bancario','deposito en'])]
    """
    return estrucutra_final;
def sort_by(e):
    return e[0]
def preprocesamiento_ngramas(request,idP):
    data = request.session["UMLDATA"]
    #ngramas = detectar_ngramas(data)
    ngramas = []
    #print("NGRAMAS")
    
    if request.method == "GET":
        
        reemplazo = []
        for i in ngramas:
            sel = request.GET.getlist(i[0])
            #print(request.GET.getlist(i[0]))
            if not sel:
                reemplazo.append((i[0],None))
            else:
                reemplazo.append((i[0],sel[0].replace(" ","")))
        #print(reemplazo)
        #print("ANTES DEL REEMPLAZO")
        #print(data)
        for i in reemplazo:
            for key in data:
                if i[1] == None:
                    break
                if key['nombre'].lower() == i[0].lower():
                    key['nombre'] = i[1]
                for relacion in range(len(key['relaciones'])):
                    print(key['relaciones'][relacion],i[0])
                    if key['relaciones'][relacion].lower() == i[0].lower():
                        print("SON IGUALES")
                        key['relaciones'][relacion] = i[1]

        #print("DESPUES DEL REEMPLAZO")
        #print(data)
        request.session["UMLDATA"] = data
        actualizar = False
        for i in reemplazo:
            if i[1] != None:
                actualizar = True
        if actualizar:
            return redirect(reverse('crearUML',kwargs={'idP':idP}))
    #print(ngramas)
    return render(request, 'ngramas.html', {'ngramas':ngramas})

############################### TESTE ##########################################
# TEST API# os.system("java -jar plantuml.jar test.txt")
####################################################################################

###########################################################################################
#CLASES
#PARA APROBECHAR POLIMORFISMO
#DEFINIR LOS FORMULARIOS VACIOS Y CON VALORES PLS
##########################################################################################
class Lel:
    def formulario(self,val):
        if val!=None:
            formulario = LEL(val)
        else:
            formulario = LEL()
        return formulario
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
class Securityscenario:
    def formulario(self,val):
        if val!=None:
            formulario = SecurityScenario(val)
        else:
            formulario = SecurityScenario()
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
    botones.append(Boton("SimilarScenarios","ScSimil"))
    botones.append(Boton("LelDetectoranstractor","lelDT"))
    return botones
    
def funcionalidadesRegitradas(request,entidadesSeleccionadas,idP):
    #REGISTRE ACA SU FUNCIONALIDAD
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
    if SimilaridadScenario.funcionalidad(entidadesSeleccionadas,request):
        return 'ScSimil'
    if LelDetector.funcionalidad(entidadesSeleccionadas,request):
        return 'lelDT'

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
    uml_clases = []
    uml_metodos = []
    uml_relaciones = []
    ################################################################
    # En uml_clases la idea es que la usen para almacenar  nombres clases
    # En uml_metodos, la idea es que almacenen diccionarios de tipo [{uml_clase: nombre_clase, uml_metodo: nombre_metodo}]
    # En uml_relaciones, la idea es que nuevamente almacenen diccionarios del tipo [{uml_clase: nombre_clase, uml_relacion: relacion(caso que no sea herencia)}, uml_subclase: relacion(caso que sea herencia)}]
    # Estas son variables de clase que seria como una "variable global" dentro de esta clase
    ################################################################
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
        detectar_ngramas(texto)
        for o in texto:
            doc = nlp(o)
            matches = matcher(doc)
            
            for match_id, start, end in matches:
                matched_span = doc[start:end]
                clasesIdentificadas.add(matched_span.lemma_.lower())
        return clasesIdentificadas


    def break_into_sentences(parrafo):
        parrafo = parrafo.replace("\\r", "¥")
        parrafo = parrafo.replace("\\n", "¥")
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

    def eliminar_tildes(self,texto: str) -> str:
        import unidecode
        return unidecode.unidecode(texto.lower())

    class Method():
        def __init__(self, className, method, originator):
            self.className = className
            self.method = method
            self.originator = originator

        def getClassName(self):
            return self.className
        
        def getName(self):
            return self.method
        
        def getOriginator(self):
            return self.originator
    
    class HierarchicalRelation():
        def __init__(self, superClass, subClass):
            self.superClass = superClass
            self.subClass = subClass

        def getClassName(self):
            return self.superClass
        
        def getSubclass(self):
            return self.subClass

    class ClassClass():
        def __init__(self, className):
            self.className = className
            self.methods = set()
            self.atributos = set()
            self.relations = set() #Relaciones no jerárquicas
            self.subclasses = set()

        def getClassName(self):
            return self.className

        def toJSON(self):
            m = set()
            for mtd in self.methods:
                m.add(mtd.getName())
                
            return {
                "nombre": self.className,
                "metodos": list(m),
                "relaciones": list(self.relations) if len(self.relations)>0 else [],
                "atributos": list(self.atributos) if len(self.atributos)>0 else [],
                "subclases": list(self.subclasses) if len(self.subclasses)>0 else []
            }

    def matchRoots(self, doc):
        matcher = DependencyMatcher(nlp_spanish.vocab)
        roots = ["ROOT", "advcl", "conj"]
        possessives = ["tener", "poseer", "haber"]
        pattern = [
            {
                "RIGHT_ID": "copula",
                "RIGHT_ATTRS": {
                    "DEP": "cop",
                    "LEMMA": {"IN": ["ser", "estar"]}
                }
            },
            {
                "LEFT_ID": "copula",
                "REL_OP": "<",
                "RIGHT_ID": "root",
                "RIGHT_ATTRS": {
                    "DEP": { "IN": roots },
                    "POS": { "IN": [ "NOUN", "ADJ" ]}
                }
            }
        ]
        matcher.add("copulative", [pattern])
        pattern = [
            {
                "RIGHT_ID": "root",
                "RIGHT_ATTRS": {
                    "DEP": {"IN": roots},
                    "POS": "VERB",
                    "LEMMA": {"IN": possessives}
                }
            }
        ]
        matcher.add("possessive", [pattern])
        pattern = [
            {
                "RIGHT_ID": "root",
                "RIGHT_ATTRS": {
                    "DEP": {"IN": roots},
                    "POS": "VERB",
                    "LEMMA": {"NOT_IN": possessives}
                }
            }
        ]
        matcher.add("action", [pattern])
        return matcher(doc)

    def isActive(self, doc):
        # IMPLEMENTAR
        return True

    def getSubjects(self, doc, matched_root):
        matcher = DependencyMatcher(nlp_spanish.vocab)
        pattern_root = {
            "RIGHT_ID": "root",
            "RIGHT_ATTRS": {
                "DEP": matched_root.dep_,
                "LEMMA": matched_root.lemma_
            }
        }
        first_subject_simple_sentence = {
                "LEFT_ID": "root",
                "REL_OP": ">",
                "RIGHT_ID": "subject",
                "RIGHT_ATTRS": {
                    "DEP": "nsubj"
                }
        }
        first_verb_complex_sentence = {
            "LEFT_ID": "root",
            "REL_OP": "<",
            "RIGHT_ID": "first verb",
            "RIGHT_ATTRS": {
                "DEP": "ROOT",
                "POS": "VERB"
            }
        }
        further_subject = {
            "LEFT_ID": "subject",
            "REL_OP": ">",
            "RIGHT_ID": "compound subject",
            "RIGHT_ATTRS": {
                "DEP": {"IN": ["conj", "appos"]},
                "POS": "NOUN"
            }
        }
        first_subject_complex_sentence = {
            "LEFT_ID": "first verb",
            "REL_OP": ">",
            "RIGHT_ID": "subject",
            "RIGHT_ATTRS": {
                "DEP": "nsubj"
            }
        }
        pattern = [
            pattern_root,
            first_subject_simple_sentence
        ]
        matcher.add("first subject simple sentence", [pattern])
        pattern = [
            pattern_root,
            first_subject_simple_sentence,
            further_subject
        ]
        matcher.add("compound subject simple sentence", [pattern])
        pattern = [
            pattern_root,
            first_verb_complex_sentence,
            first_subject_complex_sentence
        ]
        matcher.add("first subject complex sentence", [pattern])
        pattern = [
            pattern_root,
            first_verb_complex_sentence,
            first_subject_complex_sentence,
            further_subject
        ]
        matcher.add("compound subject complex sentence", [pattern])

        subjects = []
        matches = matcher(doc)
        for m in range(len(matches)):
            match_id, token_ids = matches[m]
            match nlp_spanish.vocab.strings[match_id]:
                case "compound subject complex sentence":
                    subjects.append(doc[token_ids[3]].lemma_)
                case "first subject complex sentence":
                    subjects.append(doc[token_ids[2]].lemma_)
                case "compound subject simple sentence":
                    subjects.append(doc[token_ids[2]].lemma_)
                case "first subject simple sentence":
                    subjects.append(doc[token_ids[1]].lemma_)
        return subjects

    def getDirectObjects(self, doc, matched_root):
        matcher = DependencyMatcher(nlp_spanish.vocab)
        root = {
            "RIGHT_ID": "root",
            "RIGHT_ATTRS": {
                "DEP": matched_root.dep_,
                "LEMMA": matched_root.lemma_
            }
        }
        first_object = {
                "LEFT_ID": "root",
                "REL_OP": ">",
                "RIGHT_ID": "object",
                "RIGHT_ATTRS": {
                    "DEP": "obj"
                }
        }
        pattern = [
            root,
            first_object
        ]
        matcher.add("first object", [pattern])
        pattern = [
            root,
            first_object,
            {
                "LEFT_ID": "object",
                "REL_OP": ">",
                "RIGHT_ID": "compound object",
                "RIGHT_ATTRS": {
                    "DEP": {"IN": ["conj", "appos"]},
                    "POS": "NOUN"
                }
            }
        ]
        matcher.add("compound object", [pattern])
        
        objects = []
        matches = matcher(doc)
        for m in range(len(matches)):
            match_id, token_ids = matches[m]
            if nlp_spanish.vocab.strings[match_id] == "compound object":
                objects.append(doc[token_ids[2]].lemma_)
            else:
                objects.append(doc[token_ids[1]].lemma_)
        return objects

    def findAgents(self, doc, matched_root):
        if self.isActive(self, doc):
            return self.getSubjects(self, doc, matched_root)
        """ 
        else #buscar agentes de voz pasiva
        matcher = DependencyMatcher(nlp.vocab)
        root = {
            "RIGHT_ID": "root",
            "RIGHT_ATTRS": {
                "DEP": matched_root.dep_,
                "LEMMA": matched_root.lemma_
            }
        }
        """
        return ["IS PASSIVE"]

    def findPatients(self, doc, matched_root):
        if self.isActive(self, doc):
            return self.getDirectObjects(self, doc, matched_root)
        return self.getSubjects(self, doc, matched_root)

    def identificarMetodosDeClase(self, doc):
        metodos = []
        roots = self.matchRoots(self, doc)
        for r in range(len(roots)):
            match_id, token_ids = roots[r]
            if nlp_spanish.vocab.strings[match_id] == "action":
                method_name = doc[token_ids[0]].lemma_
                agents = self.findAgents(self, doc, doc[token_ids[0]])
                patients = self.findPatients(self, doc, doc[token_ids[0]])
                for a in range(len(agents)):
                    for p in range(len(patients)):
                        metodos.append(self.Method(patients[p], method_name, agents[a]))
                    if len(patients) == 0: #Verbo intransitivo
                        metodos.append(self.Method(agents[a], method_name, None))
        return metodos

    def findOtherPredicatives(self, doc, first_subclass):
        matcher = DependencyMatcher(nlp_spanish.vocab)
        #Implementar
        pattern = [
            
        ]
        return None

    def identificarRelaciones(self, doc):
        relaciones = []
        roots = self.matchRoots(self, doc)
        for r in range(len(roots)):
            match_id, token_ids = roots[r]
            if nlp_spanish.vocab.strings[match_id] == "copulative":
                subjects = self.getSubjects(self, doc, doc[token_ids[1]])
                predicatives = [doc[token_ids[1]]]
                #predicatives.append(findOtherPredicatives(self, doc, doc[token_ids[1]]))
                for sbj in range(len(subjects)):
                    for pred in range(len(predicatives)):
                        if predicatives[pred].pos_ == "NOUN":
                            superClass = predicatives[pred].lemma_
                            subClass = subjects[sbj]
                        else:
                            superClass = subjects[sbj]
                            subClass = subjects[sbj] + "_" + predicatives[pred].lemma_
                        relaciones.append(self.HierarchicalRelation(superClass, subClass))
            elif nlp_spanish.vocab.strings[match_id] == "possession":
                #TO DO!
                pass
            
        return relaciones
    
    def getClassIndex(self, existingClasses: [ClassClass], className):
        #Recupera la clase o la crea si no existe
        for i in range(len(existingClasses)):
            if existingClasses[i].getClassName() == className:
                return i
        existingClasses.append(self.ClassClass(className))
        return len(existingClasses) - 1

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
        
        print("ESTE ES EL TEXTO QUE ENTRA:\n", texto)
        oraciones = []
        for t in texto:
            oraciones = UML.break_into_sentences(t)
        texto = oraciones
        #print("ESTE ES EL TEXTO QUE PROCESA:\n", texto)
        
        data = []
        for t in texto:
            doc = nlp_spanish(t)
            metodos = self.identificarMetodosDeClase(self, doc)
            relaciones = self.identificarRelaciones(self, doc)
            
            # Mapea clases a partir de métodos y relaciones
            classes = []
            for m in metodos:
                currentClass = self.getClassIndex(self, classes, m.getClassName())
                classes[currentClass].methods.add(m)
                classes[currentClass].relations.add(m.getOriginator())
            for r in relaciones:
                currentClass = self.getClassIndex(self, classes, r.getClassName())
                try:
                    #Encontró una relación "es un"
                    classes[currentClass].subclasses.add(r.getSubclass())
                except:
                    #Encontró una relación de composición
                    #classes[currentClass].atributos.add(r.getPossessed())
                    pass

            for c in classes:
                data.append(c.toJSON())

        print("ESTAS SON LAS CLASES QUE IDENTIFICA:")
        print(data)

        request.session["UMLDATA"] = data
        return "OK"
 
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
            request.session['textoAI'] = texto
            url = moduloneria+"/ia/"
            data ={
                "nombre": "Funcionalidad de prueba de IA",
                "texto": texto
            }

            post_response = requests.post(url, json=data)
            post_response_json = post_response.json()
            #print(post_response_json)
            listado = post_response_json


    elif (request.method == "GET") and listado:
        sel = request.GET.getlist('seleccionados')
        texto = request.session['textoAI']
        url = moduloneria+"/iaErrores/"
        data ={
                "nombre": "Funcionalidad de prueba de IA",
                "texto": texto,
                "sel" : sel
            }
        post_response = requests.post(url, json=data)
        post_response_json = post_response.json()
        #print(post_response_json)
        listado = post_response_json
        #prediccionesErroneas(request)
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
            datos = formulario.cleaned_data["texto"]
            url = moduloneria+"/recibirInputUsuario/"
            data ={
                "nombre": "Funcionalidad de prueba de IA",
                "texto": datos
            }
            post_response = requests.post(url, json=data)
            post_response_json = post_response.json()

            from app.settings import BASE_DIR
            #f = open(os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','Datos','datasetUsuario.json'),'r', encoding = 'utf-8')
            #archivo = f.read()
            #f.close()
            #archivoDesj=json.loads(archivo)
            #archivoDesj.append(json.loads(formulario.cleaned_data["texto"]))
            #print(archivoDesj)
            #with open(os.path.join(os.path.dirname(BASE_DIR), 'app', 'app','ConfigTraining','Datos','datasetUsuario.json'),'w',encoding = 'utf-8') as f:
            #    f.write(json.dumps(archivoDesj))

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
# SCENARIO SIMILARITY
#
#~#######################################################################################################
class SimilaridadScenario:
    def process_jaccardMethod(i,j):
        """
        Jaccard Similarity Method
        """
        if i == None or i == None:
            return 0
        set_i = set(i)
        set_j = set(j)
        intersection = set_i.intersection(set_j)
        union = set_i.union(set_j)
        if len(union) ==0:
            return 0 
        return (len(intersection) / len(union))

    def extract_verbs_noun_subject(text,nlp):
        """
        This method processes a generic field and return a list of words
        """
        
        doc = nlp(text)
        list_of_words=[]
        for i in doc:
            if i.pos_ =="VERB" or i.pos_=="NOUN":
                list_of_words.append(i.lemma_.lower())
        return list_of_words
    def separate_sentence(text):
        array = []
        sentence = ""
        for i in text:
            sentence+=i
            if i ==".":
                array.append(sentence)
                sentence =""
        return array
    def process_episodes(episodes,nlp):
        """
        this function processes a secuence of episodes and return a list of words
        """
        list_of_words = set()
        for i in episodes:
            list_of_words.update(SimilaridadScenario.extract_verbs_noun_subject(i,nlp))
        return list(list_of_words)
    
    def similarity(i,j,nlp):
        """
        This method processes two scenarios and return a rank
        """
        stop = set(stopwords.words('english'))
        exclude = set(string.punctuation)
        lemma = WordNetLemmatizer()
        rank_group=0
        contenido_i=json.loads(i.texto)
        contenido_j=json.loads(j.texto)
        #preprocess
        actor_i=clean(contenido_i["Actors"],stop,exclude,lemma).split()
        actor_j=clean(contenido_j["Actors"],stop,exclude,lemma).split()
        name_i = clean(i.nombre,stop,exclude,lemma).split()
        name_j = clean(j.nombre,stop,exclude,lemma).split()
        context_i = SimilaridadScenario.extract_verbs_noun_subject(contenido_i["Context"],nlp)
        context_j = SimilaridadScenario.extract_verbs_noun_subject(contenido_j["Context"],nlp)
        goal_i = SimilaridadScenario.extract_verbs_noun_subject(contenido_i["Goal"],nlp)
        goal_j = SimilaridadScenario.extract_verbs_noun_subject(contenido_j["Goal"],nlp)
        #print(contenido_i["Goal"],goal_i)
        #print(contenido_j["Goal"],goal_j)
        resources_i=clean(contenido_i["Resources"],stop,exclude,lemma).split()
        resources_j=clean(contenido_j["Resources"],stop,exclude,lemma).split()
        episodes_i = SimilaridadScenario.process_episodes(SimilaridadScenario.separate_sentence(contenido_i["Episodes"]),nlp)
        episodes_j = SimilaridadScenario.process_episodes(SimilaridadScenario.separate_sentence(contenido_j["Episodes"]),nlp)
        #process jaccard
        rank_group += SimilaridadScenario.process_jaccardMethod(actor_i,actor_j)
        rank_group += SimilaridadScenario.process_jaccardMethod(name_i,name_j)
        rank_group += SimilaridadScenario.process_jaccardMethod(context_i,context_j)
        rank_group += SimilaridadScenario.process_jaccardMethod(goal_i,goal_j)
        rank_group += SimilaridadScenario.process_jaccardMethod(resources_i,resources_j)
        rank_group += SimilaridadScenario.process_jaccardMethod(episodes_i,episodes_j)
        return (rank_group/5)
    def funcionalidad(sel,request):
        if "ScSimil" not in request.GET:
            return None
        esce=[]
        nlp = spacy.load("en_core_web_trf") 
        for i in sel:
            if Artefacto.objects.get(id=i).tipoDeArtefacto.tipo=="Scenario":
                esce.append(Artefacto.objects.get(id=i))
        def sortear(e):
            return e[0]
        filtro = set(esce)
        Scenario_set = list(filtro)
        procesados = []
        group = []
        for i in range(len(Scenario_set)):
            scenario = Scenario_set[i]
            #print(scenario)
            for j in Scenario_set:
                if j != scenario and ((scenario.nombre + j.nombre) not in procesados or (j.nombre + scenario.nombre) not in procesados):
                    rank = SimilaridadScenario.similarity(scenario,j,nlp)
                    procesados.append(scenario.nombre + j.nombre)
                    procesados.append(j.nombre + scenario.nombre)
                    group.append((rank,scenario,j))

        group.sort(key=sortear,reverse=True)
        string_resultado = []
        for i in group:
            numero = i[0]
            scena = i[1].nombre
            scenb = i[2].nombre
            string_resultado.append (f"group: {numero} scenario: {scena} {scenb}\n")
        #print(string_resultado)
        request.session["similaridad_scenarios"] = string_resultado
        return "OK"
##########################################################################################################
#
# LEL
#
#~#######################################################################################################
class LelDetector:
    def is_sentence_passive(sentence,nlp):
        matcher = Matcher(nlp.vocab)
        # Definir patrón para voz pasiva
        passive_pattern = [
            {"DEP": {"IN": ["nsubjpass", "nsubjpass:xsubj"]}},
            {"DEP": "aux", "OP": "*"},
            {"DEP": "auxpass"},
            {"TAG": "VBN"}
        ]
        matcher.add("PassivePattern", [passive_pattern])
        doc = nlp(sentence)
        matches = matcher(doc)
        return bool(matches)
    def detect_null_subject(sentence,nlp):
        doc = nlp(sentence)
        verbos = []
        for token in doc:
            if token.dep_ == "nsubj":
                verbos.append(token.text)
        if verbos:
            return False
        return True
    def detect_adjectives_and_adverbs(sentence,nlp):
        doc = nlp(sentence)
        adjectives = []
        adverbs = []

        for token in doc:
            if token.pos_ == "ADJ":
                adjectives.append(token.text)
            elif token.pos_ == "ADV":
                adverbs.append(token.text)
        if adjectives or adverbs:
            return True
        return False
    def detect_multiple_verbs(sentence,nlp):
        matcher = Matcher(nlp.vocab)
        # Definir patrón para múltiples verbos
        multiple_verbs_pattern = [
            {"POS": "VERB"},
            {"POS": "VERB", "OP": "*"}
        ]

        matcher.add("MultipleVerbsPattern", [multiple_verbs_pattern])
        doc = nlp(sentence)
        matches = matcher(doc)
        if len(matches) > 1:
            return True
        return False
    def detectar_kernel_sentence(lel,nlp):
        #print(lel)
        pasivo = LelDetector.is_sentence_passive(lel,nlp)
        #print("Pasivo: ",pasivo)
        sujeto_nulo = LelDetector.detect_null_subject(lel,nlp)
        #print("Nulo: ",sujeto_nulo)
        adjetivos_verbos = LelDetector.detect_adjectives_and_adverbs(lel,nlp)
        #print("Adjetivos y adverbios: ",adjetivos_verbos)
        multiples_verbos = LelDetector.detect_multiple_verbs(lel,nlp)
        #print("Multiples Verbos: ",multiples_verbos)
        return not (pasivo or sujeto_nulo or adjetivos_verbos or multiples_verbos)
    def separar_oraciones(lista):
        s = ""
        sentences = []
        saltear = False
        for i in lista:
            s +=i
            if i ==".":
                sentences.append(s)
                s =""
        return sentences
    def procesar_oraciones(lista,nlp):
        sentences = LelDetector.separar_oraciones(lista)
        kernel = True
        for i in sentences:
            if "if" in i or "If" in i:
                continue
            kernel = LelDetector.detectar_kernel_sentence(i,nlp)
            if kernel == False:
                return False
        return True
                
    def detectar_kernel_artefactos(lista,nlp):
        artefactos_kernel = []
        for i in lista:
            art = json.loads(i.texto)
            #print(art)
            nocion = LelDetector.detectar_kernel_sentence(art["notion"],nlp)
            impacto = LelDetector.procesar_oraciones(art["Behavioral_responses"],nlp)
            if nocion and impacto:
                artefactos_kernel.append((i,""))
            else:
                artefactos_kernel.append((i,"tiene un campo que no es kernel"))
        return artefactos_kernel
    def chequear_behavioral_responses(responses,nlp,bd_lel):
        doc = nlp(responses)
        definition = []
        comentarios =set()
        # busco lo que debo chequear
        for i in doc:
            if i.pos_ == "VERB" or i.pos_ == "NOUN":
                definition.append(i.lemma_.lower())
        faltan = []
        simbolos = []
        for i in bd_lel:
            simbolos.append(json.loads(i.texto)["nombre"].lower())
        for i in definition:
            #print(i)
            if not (i in simbolos):
                comentarios.add("NO esta definido: "+i+"\n")
        return list(comentarios)
    def etapa_dos(lista, nlp,lel_bd):
        comentarios = []
        for i in lista:
           c = LelDetector.chequear_behavioral_responses(json.loads(i[0].texto)["Behavioral_responses"],nlp,lel_bd)
           comentarios.append([json.loads(i[0].texto)["nombre"],c])
        return comentarios
    def etapa_tres(lista,nlp):
        relaciones = []
        conceptos = []
        concept = {}
        data = []
        matcher = Matcher(nlp.vocab)
        pattern = [{'POS': 'VERB', 'OP': '?'},
           {'DEP': 'pobj', 'OP': '?'}]
        matcher.add("MultipleVerbsPattern", [pattern])
        for i in lista:
            art = json.loads(i.texto)
            if art["category"] == "Subject" or art["category"] == "Object":
                n = nlp(art["nombre"].lower())
                conceptos.append(n[0].lemma_)
                concept[n[0].lemma_] = []
            elif art["category"] == "Verb":
                n = nlp(art["nombre"].lower())
                relaciones.append(n[0].lemma_)
                concept[n[0].lemma_] =[]
            # concept ["nombre"] = [relacion(verbo),relacionado con (concepto)]
        for i in lista:
            sentences = LelDetector.separar_oraciones(json.loads(i.texto)["Behavioral_responses"])
            for oracion in sentences:
                #print("ORACION")
                #print(oracion)
                doc = nlp(oracion)
                palabritas_matcheadas = []
                mat = matcher(doc)
                #print("MATCHER")
                for k in mat:
                    #print(doc[k[1]:k[2]])
                    palabritas_matcheadas.append(doc[k[1]:k[2]])
                if palabritas_matcheadas:
                    art = nlp(json.loads(i.texto)["nombre"])
                    esta =palabritas_matcheadas[0].lemma_.lower() in relaciones
                    if esta:
                        concept[art[0].lemma_].append(palabritas_matcheadas[0].lemma_.lower())
                    if len(palabritas_matcheadas)>1 and palabritas_matcheadas[1].lemma_.lower() in conceptos: #and palabritas_matcheadas[1].dep_ == "pobj":
                        try:
                            concept[palabritas_matcheadas[0].lemma_.lower()].append(palabritas_matcheadas[1].lemma_.lower())
                        except:
                            if palabritas_matcheadas[0].lemma_.lower() in conceptos:
                                concept[palabritas_matcheadas[0].lemma_.lower()]=[palabritas_matcheadas[1].lemma_.lower()]
        print(concept)
        for i in lista:
            try:
                c={
                    "nombre" : json.loads(i.texto)["nombre"],
                    "metodos":[],
                    "subclases": [],
                    "atributos":[],
                    "relaciones": concept[nlp(json.loads(i.texto)["nombre"])[0].lemma_.lower()],
                }
                data.append(c)
            except:
                pass
        #print(data)
        return data

    def funcionalidad(sel,request):

        if 'lelDT' in request.GET:
            lel=[]
            for i in sel:
                art = Artefacto.objects.get(id=i)
                if art.tipoDeArtefacto.tipo=="Lel":
                    lel.append(art)
        else: return None
        nlp = spacy.load("en_core_web_sm")
        artefactos_kernel = LelDetector.detectar_kernel_artefactos(lel,nlp)
        #print(artefactos_kernel)
        lel_bd= []
        objetos = Artefacto.objects.all()
        for i in objetos:
            if i.tipoDeArtefacto.tipo=="Lel":
                lel_bd.append(i)
        comentarios = LelDetector.etapa_dos(artefactos_kernel,nlp,lel_bd)
        data = LelDetector.etapa_tres(lel_bd,nlp)
        request.session["UMLDATA"] = data
        request.session["LELCOMENTARIOS"] = comentarios
        return "OK"




##########################################################################################################
#
# API TEST
#0
#~#######################################################################################################

class ArtefactosViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Artefacto.objects.all()
    serializer_class = ArtefactoSerializer
