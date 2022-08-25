from platform import mac_ver
from django import forms
from pkg_resources import require
from suite.models import *
##Proyectos (titulo, owner, tiposDeArtefactos)

choiceUser = []
class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['titulo','owner']
    try:
        choices = [(tipo.id,tipo.tipo) 
                   for tipo in TipoDeArtefacto.objects.all()]
    except:
        choices=[]
    titulo = forms.CharField(label='Your proyecto title', max_length=100)
    def __init__(self, *args, **kwargs):
        super(ProyectoForm, self).__init__(*args, **kwargs)
        choiceUser.append(kwargs.get('instance'))
        self.fields['owner'].initial = kwargs.get('instance')
class ElejirArtefactoAcrear(forms.Form):
    try:
        choices = [(tipo.id,tipo.tipo) 
                   for tipo in TipoDeArtefacto.objects.all()]
    except:
        choices=[]
    eleccion=forms.ChoiceField(choices=choices,initial="None")
class Busqueda(forms.Form):
    try:
        choices = [(tipo.id,tipo.tipo) 
                   for tipo in TipoDeArtefacto.objects.all()]
    except:
        choices=[]
    buscar=forms.ChoiceField(choices=choices,initial="None",label="Filtrar")
#############################################################################
#
#Formularios Personalizados
#antes que nada no hay que olvidarse de registrar el tipo de formulario en la BD
#desde el DJANGO ADMIN (sujeto a cambios)
#Para usar el Django Forms: https://docs.djangoproject.com/en/4.0/ref/forms/api/
#Registrar la opcion en el if de views.py tipoForm(sujeto a cambios)
#LA IDENTIFICACION TIENE QUE LLAMARSE NOMBRE!
#############################################################################
class textoPlano(forms.Form):
    def __init__(self, *args, **kwargs):
        super(textoPlano, self).__init__(*args, **kwargs)
        self.fields['texto'].widget.attrs['class'] = 'texto' # para el lighter
    nombre=forms.CharField(max_length=255)#<---
    texto=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}))
class Scenarios(forms.Form):
    def __init__(self, *args, **kwargs):
        super(Scenarios, self).__init__(*args, **kwargs)
    nombre=forms.CharField(max_length=255,label="ScenarioName")#<---
    Goal=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    Context=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    Resources=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    Actors=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    Episodes=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}))
class KnowledgeGraphs(forms.Form):
    nombre=forms.CharField(max_length=255,label="Nombre")
    graphOutput=forms.CharField(widget=forms.Textarea())
class UMLs(forms.Form):
    nombre=forms.CharField(max_length=255,label="Nombre")
    uml=forms.CharField(widget=forms.Textarea())

class ScenariosWithKeyWords(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ScenariosWithKeyWords, self).__init__(*args, **kwargs)
    nombre=forms.CharField(max_length=255,label="ScenarioName")#<---
    nombreKeyWords=forms.CharField(max_length=255,label="KeyWords de Name",required=False)
    Goal=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    GoalKeyWords=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}),label="KeyWords de Goal",required=False)
    Context=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    ContextKeyWords=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}),label="KeyWords de Context",required=False)
    Resources=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    ResourcesKeyWords=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}),label="KeyWords de Resources",required=False)
    Actors=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    ActorsKeyWords=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}),label="KeyWords de Actors",required=False)
    Episodes=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}))
    EpisodesKeyWords=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}),label="KeyWords de Episodes",required=False)



class ProjectFileForm(forms.Form):
    nombre = forms.CharField(max_length=50)
    file = forms.FileField() 