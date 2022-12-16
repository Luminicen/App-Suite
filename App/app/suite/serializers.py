from rest_framework import serializers
from suite.models import Artefacto,User
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']
class ArtefactoSerializer(serializers.ModelSerializer):
    owner = UsuarioSerializer() #para que no me devuelva un 1 y me devuelva almenos una desc de quien es el owner
    class Meta:
        model = Artefacto
        fields = ['nombre','texto','owner']
        #depth = 1 en el caso que tenga varios objectos entrelazados, dice hasta que nivel va a quedar en el json
        

