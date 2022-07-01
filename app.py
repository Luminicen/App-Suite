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
@cross_origin
@app.route("/passive_voice", methods=["POST"])
def passive_voice_checker():
    #print("HOLA")
    #print(request.get_json()["tipo"])
    texto= request.get_json()["texto"]
    if (re.search("podria regar tomates",texto) and re.search("HOLA SOY MIG",texto)and  (re.search("EL",texto))):
        text=[{
            "Razon":"Expresion Debil",
            "OP1":["Reemplazar por: ","puede regar tomates cuando [CONDICION]",12,32],
            "OP2":["Reemplazar por:","riega tomates",12,32],
            "tipo":"general"
            },
            {
            "Razon":"FALTAN DATOS",
            "OP1":["Reemplazar por: ","te vi tomando un gatorade",34,46],
            "tipo":"general"
            },
            {
            "Razon":"RAZON 3",
            "OP1":["Reemplazar por: ","hola mundo",47,49],
            "tipo":"general"
            }
            ]
    elif (re.search("podria regar tomates",texto) and re.search("HOLA SOY MIG",texto)and  not(re.search("EL",texto))):
        text=[{
            "Razon":"Expresion Debil",
            "OP1":["Reemplazar por: ","puede regar tomates cuando [CONDICION]",12,32],
            "OP2":["Reemplazar por:","riega tomates",12,32],
            "tipo":"general"
            },
            {
            "Razon":"FALTAN DATOS",
            "OP1":["Reemplazar por: ","te vi tomando un gatorade",34,46],
            "tipo":"general"
            }
            ]
    elif (re.search("podria regar tomates",texto) and not re.search("HOLA SOY MIG",texto)and  (re.search("EL",texto))):
        text=[{
            "Razon":"Expresion Debil",
            "OP1":["Reemplazar por: ","puede regar tomates cuando [CONDICION]",12,32],
            "OP2":["Reemplazar por:","riega tomates",12,32],
            "tipo":"general"
            },
           {
            "Razon":"RAZON 3",
            "OP1":["Reemplazar por: ","hola mundo",47,49],
            "tipo":"general"
            }
            ]
    elif (not re.search("podria regar tomates",texto) and re.search("HOLA SOY MIG",texto)and  (re.search("EL",texto))):
        text=[
            {
            "Razon":"FALTAN DATOS",
            "OP1":["Reemplazar por: ","te vi tomando un gatorade",34,46],
            "tipo":"general"
            },
            {
            "Razon":"RAZON 3",
            "OP1":["Reemplazar por: ","hola mundo",47,49],
            "tipo":"general"
            }
            ]
    elif ( re.search("podria regar tomates",texto) and not re.search("HOLA SOY MIG",texto)and  not (re.search("EL",texto))):
        text=[{
            "Razon":"Expresion Debil",
            "OP1":["Reemplazar por: ","puede regar tomates cuando [CONDICION]",12,32],
            "OP2":["Reemplazar por:","riega tomates",12,32],
            "tipo":"general"
            }
            ]
    elif ( not re.search("podria regar tomates",texto) and  re.search("HOLA SOY MIG",texto)and  not (re.search("EL",texto))):
        text=[
            {
            "Razon":"FALTAN DATOS",
            "OP1":["Reemplazar por: ","te vi tomando un gatorade",34,46],
            "tipo":"general"
            }]
    elif ( not re.search("podria regar tomates",texto) and  not re.search("HOLA SOY MIG",texto)and  (re.search("EL",texto))):
        text=[{
            "Razon":"RAZON 3",
            "OP1":["Reemplazar por: ","hola mundo",47,49],
            "tipo":"general"
            }]
    else:
        text=[]
    return jsonify(
        text
    )

@app.route("/null_subject", methods=["POST"])
def null_subject_checker():
    return jsonify(
        {"Warn": "impelementar"}
    )
#######################################REGLAS DE PRUEBA########################################
#ESTE ES SOLO UN EJEMPLO DE COMO IMPLEMENTAR LAS REGLAS
#
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
            regla["OP1"]= ["Eliminar "," " ,id,id+1]
            regla["tipo"]= "general"
            reglas.append(regla)
    return reglas
def reglaEspecifica1(campoActual,tipo,camposHermanos):
    #esta regla chequeara si los recursos estan siendo usados en los episodeos
    # aplica solo para Scenarios!
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
        #print(reglas)
        return reglas
                       
def agregarElementos(arr,elem):
    if not elem:
        return arr
    for i in elem:
        arr.append(i)
    return arr
@cross_origin
@app.route("/reglas", methods=["POST"])
def principal():
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
    #diccion(texto)
    #print("Este es el resultado que devuelve la api luego de pasar las reglas")
    #print(reglas)
    return jsonify(
        reglas,
    )
def check_word_spelling(word):
    word = Word(word)
    result = word.spellcheck()
    #print(result)
    #print(result[0])#devuelve una lista de las "posibles" soluciones al horror ortografico
    #print("-----------------")
    #if word == result[0][0]:
    #    print(f'Spelling of "{word}" is correct!')
    #else:
    #    print(f'Spelling of "{word}" is not correct!')
    #    print(f'Correct spelling of "{word}": "{result[0][0]}" (with {result[0][1]} confidence).')
    return result
def diccion(texto):
    palabras= texto.split()
    #print(palabras)
    palabras = [palabra.lower() for palabra in palabras]
    #palabras = [re.sub(r'[^A-Za-z0-9]+', '', word) for word in palabras] # elimino los simbolos de puntuacion
    pos=0
    reglas=[]
    for palabra in palabras:
        corr=check_word_spelling(palabra)
        #print(corr)
        #print("----")
        if corr[0][0] != palabra:
            #print(palabra)
            #print(corr)
            regla={}
            regla["Razon"]="misspeling"
            z=0
            for i in corr:
                regla["OP"+str(z)]= ["Reemplazar",i[0],pos,pos+len(palabra)]
                z=z+1
            regla["tipo"]= "general"
            reglas.append(regla)
        pos=pos+len(palabra)+1
    return reglas
if __name__=='__main__':
    app.run()
    