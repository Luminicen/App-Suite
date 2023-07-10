from platform import mac_ver
from django import forms
from pkg_resources import require
from suite.models import *
from django.contrib.admin.widgets import FilteredSelectMultiple
##Proyectos (titulo, owner, tiposDeArtefactos)

choiceUser = []
class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['titulo','owner','participantes']
    
    try:
        choices = [(tipo.id,tipo.tipo) 
                   for tipo in TipoDeArtefacto.objects.all()]
    except:
        choices=[]
    titulo = forms.CharField(label='Your proyecto title', max_length=100)
    participantes=forms.ModelMultipleChoiceField(queryset=User.objects.all(),
                                          label="select users",
                                          required=False,
                                          widget=FilteredSelectMultiple("participantes",False))
    class Media:
        css = {
            'all':['admin/css/widgets.css',
                   'css/uid-manage-form.css'],
        }
        # Adding this javascript is crucial
        js = ['/admin/jsi18n/']
    
    def __init__(self, *args, **kwargs):
        super(ProyectoForm, self).__init__(*args, **kwargs)
        choiceUser.append(kwargs.get('instance'))
        self.fields['owner'].initial = kwargs.get('instance')
class ElejirArtefactoAcrear(forms.Form):
    try:
        choices = [(tipo.id,tipo.tipo) 
                   for tipo in (TipoDeArtefacto.objects.all().exclude(tipo = "UML"))]
    except:
        choices=[]
    eleccion=forms.ChoiceField(choices=choices,initial="None",label="Choose")
class Busqueda(forms.Form):
    try:
        choices = [(tipo.id,tipo.tipo) 
                   for tipo in TipoDeArtefacto.objects.all()]
    except:
        choices=[]
    buscar=forms.ChoiceField(choices=choices,initial="None",label="Filter")
class Entidades(forms.Form):
    texto=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}),label="Text")
class UrlForm(forms.Form):
    url=forms.CharField(max_length=255,label="url")
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
    nombre=forms.CharField(max_length=255,label="Name")#<---
    texto=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}),label="Text")
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
    nombre=forms.CharField(max_length=255,label="Name")
    graphOutput=forms.CharField(widget=forms.Textarea())
class UMLs(forms.Form):
    nombre=forms.CharField(max_length=255,label="Name")
    uml=forms.CharField(widget=forms.Textarea())

class ScenariosWithKeyWords(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ScenariosWithKeyWords, self).__init__(*args, **kwargs)
    nombre=forms.CharField(max_length=255,label="ScenarioName")#<---
    nombreKeyWords=forms.CharField(max_length=255,label="Name's KeyWords",required=False)
    Goal=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    GoalKeyWords=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}),label="Goal's KeyWords",required=False)
    Context=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    ContextKeyWords=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}),label="Context's KeyWords",required=False)
    Resources=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    ResourcesKeyWords=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}),label="Resources 's KeyWords",required=False)
    Actors=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}))
    ActorsKeyWords=forms.CharField(max_length=255,widget=forms.Textarea(attrs={'rows': 5, 'cols': 5}),label="Actors's KeyWords",required=False)
    Episodes=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}))
    EpisodesKeyWords=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}),label="Episodes's KeyWords",required=False)

class LEL(forms.Form):
   nombre = forms.CharField(label="Name")
   category = forms.CharField(label="Category")
   notion = forms.CharField(label="Notion")
   Behavioral_responses =  forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}),label="Behavioral responses",required=False)

class ProjectFileForm(forms.Form):
    nombre = forms.CharField(max_length=50)
    file = forms.FileField()

class SecurityScenario(forms.Form):
    nombre=forms.CharField(max_length=255,label="Identification")#<---
    SourceOfStimulus=forms.CharField(max_length=255,label="Source of stimulus")
    Stimulus=forms.CharField(max_length=255,label="Stimulus")
    Environment=forms.CharField(max_length=255,label="Environment")
    Artifact=forms.CharField(max_length=255,label="Artifact")
    Response=forms.CharField(max_length=255,label="Response",required=False)
    ResponseMeasure=forms.CharField(max_length=255,label="Response Measure",required=False)
    