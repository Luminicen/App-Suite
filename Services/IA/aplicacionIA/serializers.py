from rest_framework import serializers
from aplicacionIA.models import *

class ArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artefacto
        fields = ['id', 'nombre', 'texto', 'owner', 'tipoDeArtefacto']