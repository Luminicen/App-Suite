import spacy
from spacy.tokens import DocBin
import json
archivo = open('Datos/datasetUsuario.json', encoding='utf-8').read()
TRAIN_DATA  = json.loads(archivo)
print(TRAIN_DATA)
#FALTA DATOS INNCORRECTOS
nlp = spacy.load("../Modelo_entrenado")
db = DocBin()
i=1
for text, annotations in TRAIN_DATA:
    doc = nlp(text)
    ents = []
    i+=1
    for start, end, label in annotations:
        span = doc.char_span(start, end, label=label)
        if span == None:
            print(text)
        print(span,i)
        ents.append(span)
    doc.ents = ents
    db.add(doc)
db.to_disk("./trainPlantas.spacy")