Forma de instalar la app
Paso 1: instalar librerias
pip install -r requirements.txt
Paso 2: Instalar una base de datos
Recomiendo usar xampp porque es mas sencillo iniciar o detener la bd
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