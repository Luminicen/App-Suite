import Campo from './reglasChequeoClasses.js';

document.addEventListener('DOMContentLoaded', function () {
    var fields = JSON.parse(document.getElementById('fields').textContent);
    var tipo = JSON.parse(document.getElementById('tipo').textContent)
    //console.log(fields)
    var cam=[]
    var delta=0
    let i = 0
    while(i<fields.length){
        //console.log(delta)
        cam.push(new Campo(fields[i],delta,tipo,fields))
        delta= delta + 100
        cam[i].pedirDatos()
        //setInterval(cam[i].pedirDatos(),10000)
        i = i+1
    }
    //console.log("HOLA")
    //console.log(fields.length)
    //actualizar(cam,fields.length)
    setInterval(function() {actualizar(cam,fields.length)},20000)
  })
  function actualizar(cam,len){
    let i=0
    while(i<len){
        cam[i].pedirDatosActualizar()
        i= i+1
        //console.log(i)
    }
    console.log("ACTUALIZAR")
    //setTimeout(actualizar(cam,len), 10000);
}