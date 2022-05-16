from MySQLdb import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from suite.models import *
from suite.forms import *
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
    print(escen)
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
    form=ElejirArtefactoAcrear()
    return render(request,'artefactos-lista.html',{"artifacts":escen,"ok":ok,"form":form,"idP":id})
def tipoForm(tipo,val):
    #elegirTipo
    #debe estar tal cual esta cargado en la BD
    formulario=None
    if tipo.tipo=="textoplano":
        if val!=None:
            formulario = textoPlano(val)
        else:
            formulario = textoPlano()
    elif tipo.tipo=="Scenario":
        if val!=None:
            formulario = Scenarios(val)
        else:
            formulario = Scenarios()
    else:
        if val!=None:
            formulario = textoPlano(val)
        else:
            formulario = textoPlano()
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