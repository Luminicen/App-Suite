Forma de instalar la app
Paso 1: instalar librerias
pip install -r requirements.txt
python -m spacy download en_core_web_sm
pip install rdflib
pip install wikibase_api
Paso 2: Instalar una base de datos
Recomiendo usar xampp porque es mas sencillo iniciar o detener la bd --> crear con myphpmyadmin una bd llamada "req"
Paso 3: Migrar la bd
python manage.py migrate
Paso 4: Correr el servidor
python manage.py runserver 
se puede especificar direccion ip y puerto de la siguiente forma:
python manage.py runserver [ip:port]
Paso 5: Crear usuario "root"
python manage.py createsuperuser
Paso 6: log in!
ponen en su navegador la ip que les salta y su puerto asi:
ip:puerto
Paso 7:agregar
una vez loggeado como admin, ir al sitio web admin, a Tipos de artefacto y agregar los siguientes:
textoplano
Scenario
KnowledgeGraph
ScenariosWithKeyWord
UML
ProjectFile
Lel
Securityscenario
En un futuro este paso va a desaparecer!
Siguiente paso ia:
Descargar el modelo del siguiente enlace: https://lifiainfounlpeduar-my.sharepoint.com/:u:/g/personal/jdelleville_lifia_info_unlp_edu_ar/ES4YsnwYaLZMpxzOcY2XzgABuKowWocJv9wDVtcrlH_nng?e=V4tppM
descomprimir en la carpeta donde aparece manage.py
ejecutar el script de python pysett.py
y luego ejecutar el siguiente comando:
python -m spacy train app/ConfigTraining/config.cfg --output ./output --paths.train app/ConfigTraining/Datos/trainUser.spacy --paths.dev app/ConfigTraining/Datos/trainUser.spacy
En Linux:
-si por alguna razon no te deja entrar con mysql y te salta un error de ese tipo con xampp:
ir a configuracion cambiar user name = mysql por root
.si con eso no funciona ir a app/app/app --> settings.py y reemplazar localhost por 127.0.0.1 y agregar
en allowedHost "127,0,0,1"