import Campo from './reglasChequeoClasses.js';
import Adv from './alertasDeReglas.js';
document.addEventListener('DOMContentLoaded', function () {
    var fields = JSON.parse(document.getElementById('fields').textContent);
    var tipo = JSON.parse(document.getElementById('tipo').textContent)
    var cam=[]
    var adv=[]
    var delta=0
    let i = 0
    while(i<fields.length){
        cam.push(new Campo(fields[i],delta,tipo,fields))
        adv.push(new Adv(fields[i],tipo))
        delta= delta + 100
        cam[i].pedirDatos()
        adv[i].ejecutar()
        i = i+1
    }
    setInterval(function() {actualizar(cam,fields.length,adv)},20000)
  })
  function actualizar(cam,len,adv){
    let i=0
    while(i<len){
        cam[i].pedirDatosActualizar()
        adv[i].ejecutarActualizacion()
        i= i+1
        //console.log(i)
    }
    console.log("ACTUALIZAR")
    //setTimeout(actualizar(cam,len), 10000);

}
