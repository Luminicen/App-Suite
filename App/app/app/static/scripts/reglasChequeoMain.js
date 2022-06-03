import Campo from './reglasChequeoClasses.js';

document.addEventListener('DOMContentLoaded', function () {
    var fields = JSON.parse(document.getElementById('fields').textContent);
    console.log(fields)
    var cam=[]
    var delta=0
    let i = 0
    while(i<fields.length){
        console.log(delta)
        cam.push(new Campo(fields[i],delta))
        delta= delta + 100
        cam[i].pedirDatos()
        i = i+1
    }
    console.log("CAM:")
    console.log(cam)
    //cam.push(new Campo(fields[0],delta))
    //delta = delta + 100
    //cam.push(new Campo(fields[4],delta))
    //cam[0].pedirDatos()
    //cam[1].pedirDatos()
    //console.log(cam)
    //var campo = new Campo('id_texto')
    //campo.pedirDatos()
  })