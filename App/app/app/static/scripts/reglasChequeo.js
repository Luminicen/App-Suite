window.onload = ()=>{
var ep = document.getElementById('id_texto')
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
      console.log(response.data["OP1"][3])
      $('#id_texto').highlightWithinTextarea({
        highlight: [response.data["OP1"][2], response.data["OP1"][3]]
    });
    
  });
}