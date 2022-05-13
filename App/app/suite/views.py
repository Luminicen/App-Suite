from django.shortcuts import redirect, render
from django.urls import reverse
from suite.models import *
from suite.forms import *
# Create your views here.
############################### Proyectos ##########################################
# En este lugar estaran todos los codigos del modulo de proyectos
####################################################################################
def proyectos(request):
    proyectos=Proyecto.objects.all()
    mio=[]
    ok=False
    usuario=request.user
    for p in proyectos:
        if p.owner==usuario:
            mio.append(p)
            ok=True
    print(mio)
    return render(request,'proyectos.html',{"ok":ok,"proyectos":mio})

def crearProyecto(request):
    if request.method == "POST":
        formulario = ProyectoForm(request.POST)
        if formulario.is_valid():
            print(formulario)
        #formulario.cleaned_data['owner']=request.user
            formulario.save()   
            return redirect(reverse('proyectos')) 
    else: 
        formulario = ProyectoForm(instance=request.user)
    return render(request, "proyecto-crear.html", {"form" : formulario})