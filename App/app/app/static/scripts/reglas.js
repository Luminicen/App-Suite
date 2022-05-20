
var texto="El granjero podria regar tomates."
axios({
    method: 'post',
    url: 'http://localhost:8000/proyectos/artefactos/api',
    data: {
      text: texto
    }
  }).then(function(response){
      console.log(response)
  });