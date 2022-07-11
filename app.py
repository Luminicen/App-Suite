#La idea de este archivo es mostrarles un ejemplo que funciona con la app y que lo tengan de referencia
#La app llama a una funcion principal en /reglas y esta se encarga de llamar a cada funcion regla
#para luego devolver un conjunto de cosas para marcar. Ver abajo para mas detalles!
# :D
from flask import Flask, jsonify, request
from src.endpoints.spelling_checker import SpellingChecker
from flask_cors import CORS, cross_origin
import re
import json
from textblob import Word
from requests.structures import CaseInsensitiveDict
app= Flask(__name__)
CORS(app)
@app.route("/", methods=["GET"])
def hello_world():
    return jsonify("Hola mundo!")

@app.route("/spelling", methods=["POST"])
def spelling_checker():
    checker = SpellingChecker(request.get_json()["data"])
    return jsonify(
        {
            "result": checker.check()
        }
    )

@app.route("/null_subject", methods=["POST"])
def null_subject_checker():
    return jsonify(
        {"Warn": "impelementar"}
    )

#######################################REGLAS DE PRUEBA########################################
#ESTE ES SOLO UN EJEMPLO DE COMO IMPLEMENTAR LAS REGLAS
#Se MUESTRAN EJEMPLOS CON CANTIDAD FIJA DE OPCIONES Y UNO CON CANTIDAD VARIABLE DE OPCIONES:
#regla 1, reglaEspecifica 1 y2 son de una cantidad fija de opciones
#regla de diccionario tiene cantidad variable de opciones
# Las reglas generales son las reglas que se aplican a todos los artefactos de especificacion
# Las reglas especificas se aplicana un artefacto o artefacto/s en concreto
###############################################################################################
def regla1(textito,tipo):
    #Esta regla sera de indole general, por ende todos los campos deben ser afectada por la misma
    #Se chequearan que no hayan simbolos rancios
    simbolos_rancios=["|","+","-","=","<",">"]
    reglas=[]
    for id,i in enumerate(textito):
        if i in simbolos_rancios:
            regla={}
            regla["Razon"]="Simbolo Rancio que no deberia estar ahi"
            regla["OP1"]= ["Eliminar "," " ,id,id+1] #cantidad fija de opciones!
            regla["tipo"]= "general"
            reglas.append(regla)
    return reglas
def reglaEspecifica1(campoActual,tipo,camposHermanos):
    #esta regla chequeara si los recursos estan siendo usados en los episodeos
    # aplica solo para Scenarios!
    # utiliza mas de un campo!
    if tipo=="Scenario" and campoActual=="id_Resources":
        reglas=[]
        palabraActual=0
        for i in camposHermanos["id_Resources"].split(","):
            if not (re.search(i.lower(),camposHermanos["id_Episodes"].lower())):
                regla={}
                regla["Razon"]="Este Recurso no ha sido mensionado en ningun Episodeo"
                regla["OP1"]= ["Eliminar"," ",palabraActual,palabraActual+len(i)]
                regla["tipo"]= "Scenario"
                reglas.append(regla)
            palabraActual=palabraActual + len(i) + 1
        #print(reglas)
        return reglas
def reglaEspecifica2(campoActual,tipo,camposHermanos):
    #esta regla chequeara si los actores estan siendo usados en los episodeos
    # aplica solo para Scenarios!
    # utiliza mas de un campo!
    if tipo=="Scenario" and campoActual=="id_Actors":
        reglas=[]
        palabraActual=0
        for i in camposHermanos["id_Actors"].split(","):
            if not (re.search(i.lower(),camposHermanos["id_Episodes"].lower())):
                regla={}
                regla["Razon"]="Este Actor no ha sido mensionado en ningun Episodeo"
                regla["OP1"]= ["Eliminar"," ",palabraActual,palabraActual+len(i)]
                regla["tipo"]= "Scenario"
                reglas.append(regla)
            palabraActual=palabraActual + len(i) + 1
        return reglas
                       
def agregarElementos(arr,elem):
    #lo unico que hace es fucionar los arreglos de cosas marcadas
    #nada interesante por aca...
    if not elem:
        return arr
    for i in elem:
        arr.append(i)
    return arr
@cross_origin
@app.route("/reglas", methods=["POST"])
def principal():
    #funcion principal que llama a las reglas (ES UN EJEMPLO)
    #mi app llamara a esta funcion y esta funcion llamara a las reglas
    #cada regla devuelve un arreglo de lo que hay que marcar
    #cada arreglo se une en un unico arreglo que es devuelto a la app
    #en el formato que espera:
    #Formato de una sola regla:
    #{
    #   Razón: "RAZÓN DE LA RELGA, ¿Por qué se marco?”
    #   OP1:[”Reemplaza”,”Lo que debe ir o piensa que va a ir”,inicio_reemplazo,Fin_Reemplazo]
    #   …
    #   OPN:[”Reemplaza”,”Lo que debe ir o piensa que va a ir”,inicio_reemplazo,Fin_Reemplazo]
    #   Tipo=“general o especifico de algún formulario”
    #}
    # Formato que espera la app: [{regla1},{regla2}, ... ,{regla N}] o [] (si no se marca nada)
    #Cualquier cosa consulten!
    reglas=[]
    try:
        camposAdicionales=json.loads(request.get_json()["adicional"])
    except:
        camposAdicionales=None
    #print("Esto es lo que recibe la api: ")
    #print(request.get_json())
    texto=request.get_json()["texto"]
    tipo=request.get_json()["tipo"]
    campoActual=request.get_json()["yoSoy"]
    #registre sus reglas aca!
    reglas=agregarElementos(reglas,reglaEspecifica1(campoActual,tipo,camposAdicionales))
    reglas=agregarElementos(reglas,reglaEspecifica2(campoActual,tipo,camposAdicionales))
    reglas=agregarElementos(reglas,regla1(texto,tipo))
    reglas=agregarElementos(reglas,diccion(texto))
    #print("Este es el resultado que devuelve la api luego de pasar las reglas")
    #print(reglas)
    return jsonify(
        reglas,
    )
def check_word_spelling(word):
    word = Word(word)
    result = word.spellcheck()
    return result
def diccion(texto):
    #Ejemplo con multiOpcion variable
    #La idea es encontrar horrores de ortografia y dar un conjunto
    #de soluciones para corregir dicho error
    palabras= texto.split()
    palabras = [palabra.lower() for palabra in palabras]
    pos=0
    reglas=[]
    for palabra in palabras:
        corr=check_word_spelling(palabra)
        if corr[0][0] != palabra:
            regla={}
            regla["Razon"]="misspeling"
            z=0
            for i in corr:
                regla["OP"+str(z)]= ["Reemplazar",i[0],pos,pos+len(palabra)]#Las opciones varian
                z=z+1
            regla["tipo"]= "general"
            reglas.append(regla)
        pos=pos+len(palabra)+1
    return reglas
if __name__=='__main__':
    app.run()
    