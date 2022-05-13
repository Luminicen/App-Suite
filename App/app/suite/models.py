from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class TipoDeArtefacto(models.Model):
    #esto es para identificar el tipo de texto
    tipo = models.CharField(max_length=255,blank=False)
    descripcion=models.CharField(max_length=255)
    def __str__(self):
        return f"Tipo {self.tipo}"
class Proyecto(models.Model):
    #Proyectos (titulo, owner, tiposDeArtefactos)
    #cada proyecto tiene varios artefactos
    titulo=models.CharField(max_length=255,blank=False)
    owner=models.ForeignKey(User, on_delete=models.CASCADE)
    artefactos=models.ManyToManyField("Artefacto",blank=True)
    def __str__(self):
        return f"Proyecto {self.titulo} de {self.owner.username}"
class Artefacto(models.Model):
    #artefactos (texto owner, tipoDeArtefacto)
    #los textos de cualquier tipo :P
    nombre = models.CharField(max_length=255,blank=False)
    texto = models.TextField()
    owner= models.ForeignKey(User, on_delete=models.CASCADE)
    tipoDeArtefacto= models.ForeignKey('tipoDeArtefacto', on_delete=models.CASCADE)
    def __str__(self):
        return f"Texto de tipo {self.tipoDeArtefacto.titulo} de {self.owner.username} llamado {self.nombre}"