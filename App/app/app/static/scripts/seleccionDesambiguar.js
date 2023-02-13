var instervalos = []
var archivo=[document.getElementById("id_texto").value,new Set()]
//[texto, [[inicio, fin, tag], [inicio, fin, tag2]]
function selection(){
    if (window.getSelection){
        var range = window.getSelection ();
        return window.getSelection();
           
    }}
function dispararTaggeo(tag){
    texto = document.getElementById("id_texto").value
    let seleccion = selection()
    let a
    let intervalo=DevolverPosicioncaracteres(seleccion,texto)
    archivo[0] = texto
    a = seleccion.toString()
    archivo[1].add(a)
    instervalos.push(intervalo)
    $('#id_texto').highlightWithinTextarea({
        highlight: Array.from(archivo[1])
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
    archivo=[document.getElementById("id_texto").value,new Set()]
    $('#id_texto').highlightWithinTextarea({
        highlight: instervalos
      });
}
const element = document.querySelector('form');
element.addEventListener('submit', event => {
    archivo[1]=Array.from(archivo[1])
    document.getElementById("id_texto").value = JSON.stringify(archivo)
});
