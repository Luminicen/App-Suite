from cgitb import text
from MySQLdb import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from suite.models import *
from suite.forms import *
import requests as req
import json
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
            print(formulario)
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
        sel = request.GET.getlist('seleccionados')
        funcionalidadesRegitradas(request,sel)
    botones=listaBotones()
    form=ElejirArtefactoAcrear()
    return render(request,'artefactos-lista.html',{"artifacts":escen,"ok":ok,"form":form,"idP":id,"botones":botones})
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

    return render(request, "proyecto-crear.html", {"form" : form})

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
    return render(request, "proyecto-crear.html", {"form" : form})

def destruirArtefacto(request,id,idP):
    artefacto= Artefacto.objects.get(id=id)
    proyecto= Proyecto.objects.get(id=idP)
    proyecto.artefactos.remove(artefacto)
    artefacto.delete()
    return redirect(reverse('artefactos',kwargs={'id':idP}))


    

############################### TESTE ##########################################
# TEST API
####################################################################################
def reglaSimpleParaTextoPlano(text):
    # El granjero podria regar tomates.
    text={
        "Razon":"Expresion Debil",
        "OP1":["Reemplazar por: ","puede regar tomates cuando [CONDICION]",13,-1],
        "OP2":["Reemplazar por:","riega tomates",13,-1],
        "palabraAMarcar":"podria"
        }
    return text
def consumirApi(texto):
    rta=req.post("http://127.0.0.1:5000/passive_voice",texto)
    dec=json.loads(rta.text)
    print(dec)
    pass
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
                formatoToKG(esce)
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