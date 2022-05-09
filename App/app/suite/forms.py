from django import forms
from suite.models import *
##Proyectos (titulo, owner, tiposDeArtefactos)


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['titulo','owner']
    choices = [(tipo.id,tipo.tipo) 
                   for tipo in TipoDeArtefacto.objects.all()]
    choices1=[]
    titulo = forms.CharField(label='Your proyecto title', max_length=100)
    def __init__(self, *args, **kwargs):
        super(ProyectoForm, self).__init__(*args, **kwargs)
        self.fields['owner'].initial = kwargs.get('instance')