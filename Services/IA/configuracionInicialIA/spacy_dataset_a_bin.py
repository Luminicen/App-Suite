import spacy
from spacy.tokens import DocBin
import json
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
archivo = open(os.path.join(os.path.dirname(BASE_DIR),'IA','configuracionInicialIA','datasetInicial.json'), encoding='utf-8').read()
TRAIN_DATA  = json.loads(archivo)
#print(TRAIN_DATA)
#FALTA DATOS INNCORRECTOS
nlp = spacy.load("en_core_web_sm")
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
        if span != None:
            ents.append(span)
    doc.ents = ents
    db.add(doc)
db.to_disk(os.path.join(os.path.dirname(BASE_DIR),'IA','configuracionInicialIA','trainData.spacy'))