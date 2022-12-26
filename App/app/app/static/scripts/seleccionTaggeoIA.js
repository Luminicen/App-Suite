var instervalos = []
var archivo=[document.getElementById("id_texto").value,[]]
//[texto, [[inicio, fin, tag], [inicio, fin, tag2]]
function selection(){
    if (window.getSelection)
           return window.getSelection();
    }
function dispararTaggeo(tag){
    texto = document.getElementById("id_texto").value
    let mostrar = document.getElementById("mostrar")
    let seleccion = selection()
    mostrar.innerHTML = "Ultimo seleccionado "+seleccion + " " +tag;
    let intervalo=DevolverPosicioncaracteres(seleccion,texto)
    archivo[0] = texto
    archivo[1].push([intervalo[0],intervalo[1],tag])
    instervalos.push(intervalo)
    $('#id_texto').highlightWithinTextarea({
        highlight: instervalos
      });
    console.log(archivo)
}
function DevolverPosicioncaracteres(seleccion,texto){
    let str = texto
    let searchStr = seleccion
    let result = str.indexOf(searchStr);
    return [result,result+seleccion.toString().length]
}
function limpiar(){
    instervalos = []
    archivo=[document.getElementById("id_texto").value,[]]
    $('#id_texto').highlightWithinTextarea({
        highlight: instervalos
      });
}
const element = document.querySelector('form');
element.addEventListener('submit', event => {
    document.getElementById("id_texto").value = JSON.stringify(archivo)
});
