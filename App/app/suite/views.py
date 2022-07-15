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


############################### Escenarios ##########################################
# En este lugar estaran todos los codigos del modulo de Escenarios
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
        funcionalidadesRegitradas(request,sel)
    botones=listaBotones()
    return render(request,'artefactos-lista.html',{"artifacts":escen,"ok":ok,"form":form,"formB":form2,"idP":id,"botones":botones})
def tipoForm(tipo,val):
    #elegirTipo
    #debe estar tal cual esta cargado en la BD
    formulario=None
    formulario=globals()[tipo.tipo]().formulario(val)
    if formulario==None:
        raise("TE OLVIDASTE DE CONFIGURAR LA FUNCION TIPO FORM GIL")
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
    ##print(type(get_all_fields_from_form(form)))
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
class Scenario:
    def formulario(self,val):
        if val!=None:
            formulario = Scenarios(val)
        else:
            formulario = Scenarios()
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
    botones.append(Boton("TO KNOWLEDGE GRAPH","kg"))
    botones.append(Boton("DUMMY","dm"))
    return botones
def funcionalidadesRegitradas(request,entidadesSeleccionadas):
    #REGISTRE ACA SU FUNCIONALIDAD
    #paradigma por broadcast event based
    KG.knowledgeGraph(entidadesSeleccionadas,request)
    dumy.funcionalidad(entidadesSeleccionadas,request)

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