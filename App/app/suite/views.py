from io import StringIO
import mimetypes
import os
import webbrowser
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
nlp = spacy.load("es_dep_news_trf")
# Create your views here.
############################### Permisos ##########################################
# Codigos de los permisos
####################################################################################
def tienePermiso(user,proyecto):
    if (proyecto.owner==user) or (user in proyecto.participantes.all()):
        return True
    return False
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
    return render(request, "proyecto-crear.html", {"form" : formulario})
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
            proyecto.save()   
            return redirect(reverse('proyectos')) 
    else:
        datosAModificar={'titulo': proyecto.titulo,'owner':proyecto.owner,'participantes':proyecto.participantes.all()}
        formulario = ProyectoForm(datosAModificar,instance=request.user,initial=datosAModificar)
    return render(request, "proyecto-crear.html", {"form" : formulario})


############################### arte4facto ##########################################
# En este lugar estaran todos los codigos del modulo de artefacto
####################################################################################
def artefactos(request,id):
    proyecto=Proyecto.objects.get(id=id)
    escen= proyecto.artefactos.all()
    if not tienePermiso(request.user,proyecto):
        return render(request,'ERRORES/403.html',{})
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
    return render(request, "proyecto-crear.html", {"form" : form,"campos":fields,"tipo":tipo.tipo})


def modificarArtefacto(request,id,idP):
    artefacto= Artefacto.objects.get(id=id)
    texto=json.loads(artefacto.texto)
    if request.method == "POST":
        formulario = form=tipoForm(artefacto.tipoDeArtefacto,request.POST)
        if formulario.is_valid():
            infForma=formulario.cleaned_data
            aux=json.dumps(infForma,indent=4)
            artefacto.nombre=infForma['nombre']
            artefacto.texto=aux
            artefacto.save()
            return redirect(reverse('artefactos',kwargs={'id':idP}))
    else:
        #uso None para inicializar un form vacio
        form=tipoForm(artefacto.tipoDeArtefacto,texto)
    #queda llenar el form y mandarlo como siempre
    all_fields = form.declared_fields.keys()
    fields=[]
    for i in all_fields:
        if i != 'nombre':
            fields.append('id_'+i)
    return render(request, "proyecto-crear.html", {"form" : form,"campos":fields,"tipo":artefacto.tipoDeArtefacto.tipo})

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
    return render(request, "proyecto-crear.html", {"form" : form,"campos":fields,"tipo":tipo.tipo})

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
    botones.append(Boton("Crear grafo de conocimiento","kg"))
    botones.append(Boton("A UML","uml"))
    botones.append(Boton("Convertir a ScenarioKeyWords","cskw"))
    botones.append(Boton("Exportar Scenario con keywords a txt","exportSKW"))
    botones.append(Boton("Validar grafo de requerimientos","shacl4j"))
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
    @classmethod
    def identificarClases(self,texto):
        matcher = Matcher(nlp.vocab)
        pattern = [{"POS": "NOUN"}]
        matcher.add("Class Candidate", [pattern])
        pattern = [{"DEP": {"IN": ["nsubj", "dobj", "iobj"]}}]
        matcher.add("Class Candidate", [pattern])
        clasesIdentificadas = set()
        for o in texto:
            doc = nlp(o)
            matches = matcher(doc)
            for match_id, start, end in matches:
                matched_span = doc[start:end]
                clasesIdentificadas.add(matched_span.lemma_.lower())
        return clasesIdentificadas

    @classmethod
    def identificarMetodosDeClase(self,clases,texto):
        verbosProhibidos = ["contener", "ser", "es"]
        metodosDeClaseIdentificados = []
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
                                repetido["metodos"].append(verbToken.lemma_)
        return metodosDeClaseIdentificados
    def identificarRelaciones(self,clases,texto):

        def buscarSiYaExiste(sustantivo,relacionesIdentificados):
            for palabra in relacionesIdentificados:
                if(palabra["nombre"]==sustantivo): 
                    return True
            return False

        def evaluarPalabra(sustantivo,sustantivoRelacion,relaciones,esHerencia):
            if(not(buscarSiYaExiste(sustantivo,relaciones))):
                palabra = {
                            "nombre": sustantivo, 
                            "relacion":[], 
                            "subclase": []
                        }
                relaciones.append(palabra)
            for palabra in relaciones:
                if(palabra["nombre"]==sustantivo): 
                    if esHerencia:
                        palabra["subclase"].append(sustantivoRelacion)
                    else:
                        palabra["relacion"].append(sustantivoRelacion)

        matcher = Matcher(nlp.vocab)
        pattern_subclase = [{'POS': {"IN":['NOUN','ADJ']}}, {'POS': 'AUX'}, {'POS': {"IN":['NOUN','PROPN']}}]
        pattern_conoc = [{'POS': {"IN":['NOUN','PROPN','VERB','ADJ']}}, {'POS': 'VERB'}, {'POS': 'NOUN'}]
        matcher.add("conocimiento", [pattern_conoc])
        matcher.add("subclase", [pattern_subclase])
        relacionesIdentificadas=[]
        for o in texto:
            doc = nlp(o)
            matches = matcher(doc)
            for match_id, start, end in matches:
                sustantivo1= doc[start:start+1].text.lower()
                sustantivo2= doc[end-1:end].text.lower()
                verb = doc[start + 1:end - 1].text.lower()
                if(sustantivo1,sustantivo2 in clases):
                    if verb =="ser":
                        evaluarPalabra(sustantivo2,sustantivo1,relacionesIdentificadas,True)
                    else:
                        evaluarPalabra(sustantivo1,sustantivo2,relacionesIdentificadas,False)           
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
        #print(texto)
        #texto es un arreglo con los textos que vienen seleccionados
        if not texto:
            return None
        aux=[]
        for i in texto:
            aux.append(self.eliminar_tildes(self,i))
        texto=aux
        clases=tranfSetArr(UML.identificarClases(texto))
        metodos=UML.identificarMetodosDeClase(clases,texto)
        
        relaciones=UML.identificarRelaciones(self,clases,texto)
        data=[]
        #expression_if_true if condition else expression_if_false
        #print(clases)
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
    def convertidor(escenario,request,idP):
        cont=json.loads(escenario.texto)
        escKW={
            "nombre":cont["nombre"],
            "nombreKeyWords":" ",
            "Goal":cont["Goal"],
            "GoalKeyWords":" ",
            "Context":cont["Context"],
            "ContextKeyWords":" ",
            "Resources":cont["Resources"],
            "ResourcesKeyWords":" ",
            "Actors":cont["Actors"],
            "ActorsKeyWords":" ",
            "Episodes": cont["Episodes"],
            "EpisodesKeyWords":" "
        }
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
        
