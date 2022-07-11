import Campo from './reglasChequeoClasses.js';
document.addEventListener('DOMContentLoaded', function () {
    var fields = JSON.parse(document.getElementById('fields').textContent);
    var tipo = JSON.parse(document.getElementById('tipo').textContent)
    var cam=[]
    var delta=0
    let i = 0
    while(i<fields.length){
        cam.push(new Campo(fields[i],delta,tipo,fields))
        delta= delta + 100
        cam[i].pedirDatos()
        i = i+1
    }
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
