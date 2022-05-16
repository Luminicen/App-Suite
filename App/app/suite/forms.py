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
    choices = [(tipo.id,tipo.tipo) 
                   for tipo in TipoDeArtefacto.objects.all()]
    titulo = forms.CharField(label='Your proyecto title', max_length=100)
    def __init__(self, *args, **kwargs):
        super(ProyectoForm, self).__init__(*args, **kwargs)
        choiceUser.append(kwargs.get('instance'))
        self.fields['owner'].initial = kwargs.get('instance')
class ElejirArtefactoAcrear(forms.Form):
    choices = [(tipo.id,tipo.tipo) 
                   for tipo in TipoDeArtefacto.objects.all()]
    eleccion=forms.ChoiceField(choices=choices)
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
    nombre=forms.CharField(max_length=255)#<---
    texto=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}))
class Scenarios(forms.Form):
    nombre=forms.CharField(max_length=255,label="ScenarioName")#<---
    Goal=forms.CharField(max_length=255)
    Context=forms.CharField(max_length=255)
    Resources=forms.CharField(max_length=255)
    Actors=forms.CharField(max_length=255)
    Episodes=forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 85}))