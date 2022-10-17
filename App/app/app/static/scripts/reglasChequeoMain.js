import CampoV2 from './highlighterverstwo.js';
import Adv from './alertasDeReglas.js';
//para volver a activar el highlighter, descomentar cam
document.addEventListener('DOMContentLoaded', function () {
    var boton
    var fields = JSON.parse(document.getElementById('fields').textContent);
    var tipo = JSON.parse(document.getElementById('tipo').textContent)
    var cam=[]
    var adv=[]
    var delta=0
    let i = 0
    while(i<fields.length){
        cam.push(new CampoV2(fields[i],delta,tipo,fields))
        adv.push(new Adv(fields[i],tipo))
        delta= delta + 100
        cam[i].pedirDatos()
        adv[i].ejecutar()
        i = i+1
    }
    boton = document.getElementById("corrector")
    if (boton != null){
        boton.addEventListener("click", function(){actualizar(cam,fields.length,adv)});
    }
    //setInterval(function() {actualizar(cam,fields.length,adv)},20000)
})

  function actualizar(cam,len,adv){
    let i=0
    while(i<len){
        //cam[i].actualizar()
        adv[i].ejecutarLimpieza()
        i= i+1
        //console.log(i)
    }
    console.log("ACTUALIZAR")
}

