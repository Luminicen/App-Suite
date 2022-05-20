window.onload = ()=>{
var ep = document.getElementById('id_Episodes')
console.log(ep.value)
var texto=ep.value
axios({
    method: 'post',
    url: 'http://localhost:5000/passive_voice',
    data: {
      text: texto
    }
  }).then(function(response){
      console.log(response)
  });
}