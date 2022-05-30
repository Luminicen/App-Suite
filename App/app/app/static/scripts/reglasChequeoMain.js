import Campo from './reglasChequeoClasses.js';

document.addEventListener('DOMContentLoaded', function () {
    var fields = JSON.parse(document.getElementById('fields').textContent);
    var cam=[]
    let i = 0
    while(i<fields.length){
        cam.push(new Campo(fields[i]))
        cam[i].pedirDatos()
        i = i+1
    }
    console.log(cam)
    //var campo = new Campo('id_texto')
    //campo.pedirDatos()
  })