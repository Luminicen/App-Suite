from cgitb import text
from MySQLdb import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from suite.models import *
from suite.forms import *
#import requests as req
import json
from suite.ontoscen.wikilink import Wikilink
from suite.ontoscen.ontoscen import Ontoscen
from suite.ontoscen.requirement import Requirement
# Create your views here.
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
    return render(request,'proyectos.html',{"ok":ok,"proyectos":mio})

def crearProyecto(request):
    #creo el formulario proyecto y lo mando al template
    #si el form tiene datos invalidos creo el objeto y guardo en bd
    if request.method == "POST":
        formulario = ProyectoForm(request.POST)
        if formulario.is_valid():
            #print(formulario)
            formulario.save()   
            return redirect(reverse('proyectos')) 
    else: 
        formulario = ProyectoForm(instance=request.user)
    return render(request, "proyecto-crear.html", {"form" : formulario})
def eliminarProyecto(request,id):
    #obtengo el proyecto a eliminar por id y lo elimino
    proyecto=Proyecto.objects.get(id=id)
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
        datosAModificar={'titulo': proyecto.titulo,'owner':proyecto.owner}
        formulario = ProyectoForm(datosAModificar,instance=request.user,initial=datosAModificar)
    return render(request, "proyecto-crear.html", {"form" : formulario})


############################### arte4facto ##########################################
# En este lugar estaran todos los codigos del modulo de artefacto
####################################################################################
def artefactos(request,id):
    proyecto=Proyecto.objects.get(id=id)
    escen= proyecto.artefactos.all()
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
        print(request.GET)
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
def crearArtefactos(request,idP,idT):
    #idP = id del Proyecto
    #idT = id del Tipo
    proyecto=Proyecto.objects.get(id=idP)
    tipo=TipoDeArtefacto.objects.get(id=idT)
    if request.method == "POST":
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
    print("ENTRO A CREAR ARTEFACTOKG")
    proyecto=Proyecto.objects.get(id=idP)
    tipo=TipoDeArtefacto.objects.get(tipo='KnowledgeGraph')
    if request.method == "POST":
        formulario = KnowledgeGraphs(request.POST)
        print(formulario)
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
    botones.append(Boton("A Grafo de Conocimiento","kg"))
    botones.append(Boton("A UML","uml"))
    botones.append(Boton("Convertir a ScenarioKeyWords","cskw"))
    return botones
def funcionalidadesRegitradas(request,entidadesSeleccionadas,idP):
    #REGISTRE ACA SU FUNCIONALIDAD
    #paradigma por broadcast event based
    if KG.knowledgeGraph(entidadesSeleccionadas,request):
        return 'kg'
    if UML.funcionalidad(entidadesSeleccionadas,request):
        return 'uml'
    if TransformarAScenariosKeyWords.funcionalidad(entidadesSeleccionadas,request,idP):
        return 'cskw'

class KG():
    def knowledgeGraph(sel,request):
        if 'kg' in request.GET:
            esce=[]
            for i in sel:
                if Artefacto.objects.get(id=i).tipoDeArtefacto.tipo=="Scenario":
                    esce.append(i)
            print(esce)
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
    print(json.loads(textF))
    return textF
def separarPorComa(actoresStr):
    lista=[]
    lista.extend(actoresStr.split(","))
    return lista
def separarPorPunto(actoresStr):
    lista=[]
    lista.extend(actoresStr.split("."))
    return lista
class dumy:
    def funcionalidad(ent,request):
         if 'dm' in request.GET:
            print("SOY DUMMY")
            return "SI"
class UML:
    @classmethod
    def identificarClases(self,texxto):
        clasesIdentificadas=[]
        #SU CODIGO
        clasesIdentificadas=["empresa", "travesia", "kayakista", "itinerario", "costo", "lugar", "expert", "inexperto"]
        return clasesIdentificadas
    @classmethod
    def identicarMetodosDeClase(self,clases,texto):
        metodosDeClaseIdentificados={}
        #SU CODIGO
        metodosDeClaseIdentificados={"travesia":["ofrecer", "contratar"]}
        return metodosDeClaseIdentificados
    @classmethod
    def identificarRelaciones(self,clases,texto):
        relacionesIdentificadas={}
        #SU CODIGO
        relacionesIdentificadas={"empresa":{"conoce":["travesia"],"subclase":[]},"kayakista":{"conoce":["travesia"],"subclase":["experto","inexperto" ]},"travesia":{"conoce":["itinerario","costo"],"subclase":[]}}
        return relacionesIdentificadas
    @classmethod
    def funcionalidad(self,sel,request):
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
        texto=["""empresa ofrecer travesía.
                  Kayakista contratar travesía.
                  Travesia contener itinerario.
                  Travesia contener costo.
                  Itinerario contener lugar.
                  Experto ser kayakista.
                  Inexperto ser kayakista.
                """]
        #print(texto)
        #texto es un arreglo con los textos que vienen seleccionados
        if not texto:
            return None
        clases=UML.identificarClases(texto)
        metodos=UML.identicarMetodosDeClase(clases,texto)
        relaciones=UML.identificarRelaciones(clases,texto)
        data=[]
        for clase in clases:
            arr=[]
            if clase in metodos:
                arr.append(metodos[clase])
            if clase in relaciones:
                arr.append(relaciones[clase])
            c={clase : arr}
            data.append(c)
        #data es lo que devolveria luego del procesamiento
        #print(data)
        return data
class TransformarAScenariosKeyWords:
    #CONVIERTE UN ESCENARIO NORMAL A UNO CON KEYWORDS
    def funcionalidad(sel,request,idP):
        if 'cskw' in request.GET:
            esce=[]
            for i in sel:
                if Artefacto.objects.get(id=i).tipoDeArtefacto.tipo=="Scenario":
                    esce.append(i)
            print(esce)
            for i in esce:
                TransformarAScenariosKeyWords.convertidor(Artefacto.objects.get(id=i),request,idP)
            return "OK"
        else:
            return None
    def convertidor(escenario,request,idP):
        cont=json.loads(escenario.texto)
        escKW={
            "nombreKeyWords":" ",
            "Goal":cont["Context"],
            "GoalKeyWords":" ",
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

        