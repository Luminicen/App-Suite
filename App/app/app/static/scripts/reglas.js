//rta=req.post("http://127.0.0.1:5000/passive_voice",texto)
var texto="El granjero podria regar tomates."
axios({
    method: 'post',
    url: 'http://127.0.0.1:5000/passive_voice',
    data: {
      text: texto
    }
  }).then(function(response){
      console.log(response)
  });