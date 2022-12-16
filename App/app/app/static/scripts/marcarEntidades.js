var palabras_a_marcar = JSON.parse(document.getElementById('tipo').textContent)
let largoD = 0
let largoTotal = palabras_a_marcar.length
let arr = []
while (largoD < (largoTotal)){
    arr.push(
    {
        highlight: palabras_a_marcar[largoD],
        className: 'entidad'
    })  
    largoD = largoD + 1
}
$('#id_texto').highlightWithinTextarea({
    highlight: arr
  });