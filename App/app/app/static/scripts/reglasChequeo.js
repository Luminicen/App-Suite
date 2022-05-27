window.onload = ()=>{
var ep = document.getElementById('id_texto')
console.log(ep.value)
var Boundaries
var contextMenu
var texto=ep.value
var long=0
var arr=[]
var arrContext=[]
var arrbonds=[]
var arrOP=[] // voy a tener siempre una razon, lo que me varian son las opciones
//ESPECIFICACIONES
//CADA REGLA ME TIENE QUE VENIR DE LA FORMA ESCRITA EN LOS PPT
//Por defecto van a nombrarse solas como reglaNumero para los highlighters
axios({
    method: 'post',
    url: 'http://localhost:5000/passive_voice',
    data: {
      text: texto
    }
  }).then(function(response){
      console.log(response)
      //GENERO LOS DATOS PARA PASARSELO AL HIGHLIGHTER
      long=response.data.length - 1
      crearArregloDeHighlights(long,arr,arrOP,response)
      //al elemento (TEXT AREA) le mando lo que hay que marcar
      $ep.highlightWithinTextarea({
        highlight: arr
    });
    //console.log("HOLA 3")
    //console.log(response.data[2]["Razon"])

    //MENU CONTEXTUAL
    configuracionDeMenuesContextuales(contextMenu,response,arrContext,arrbonds,long)
    

  });
    //un listener que cieerre todos los menus contextuales :D
    ep.addEventListener('click', function(e){e.preventDefault();
      q=0 
      while(q<=long){arrContext[q].closeMenu();q= q + 1}
      
      });
function crearArregloDeHighlights(long,arr,arrOP,response){
  let largoD= 0
      while (largoD < (long+1)){
        //Realizo la carga de datos al arreglo que va a tener highlights
        arr.push({highlight: [response.data[largoD]["OP1"][2], response.data[largoD]["OP1"][3]],
        className: 'regla'+largoD})
        z=1
        arrOP[largoD]=0
        while (response.data[largoD]["OP"+z] != undefined){
            arrOP[largoD]= arrOP[largoD] + 1
            z = z + 1
          }
          
        
        largoD = largoD + 1
      }
}
function configuracionDeMenuesContextuales(contextMenu,response,arrContext,arrbonds,long){
  let largo = 0
    //le asigno al que esta marcado un menu de contexto y le agrego las opciones
    while (largo < (long+1)) {
      crearMenusContextuales(largo,contextMenu,response,arrContext)

    //ACA COMIENZA EL LIO
    //como tengo un problema de capas, porque al hacer click no le estoy haciendo click al elemento
    //realmente marcado (que es el clon del text area con el elemento a marcar entre <MARK>) sino que
    //le estoy haciendo click al text area comun (donde escribo)
    //La SOLUCION: saco las coords x e y y si yo clickeo ahi es porque estoy clickeando al elemento
    //marcado.
      crearBoundariesParaMenuesContextuales(largo,arrbonds,long)
    largo = largo + 1
    }
}

function crearMenusContextuales(largo,contextMenu,response,arrContext){
  contextMenu = CtxMenu(document.querySelectorAll('.regla'+largo)[0]);
  //le inserto el primer item que es la razon por la que se marco
  contextMenu.addItem(response.data[largo]["Razon"])
  contextMenu.addSeparator(index = 1)
  p=1
  //le inserto los reemplazos con la funcion de reemplazo correspondiente
  while(response.data[largo]["OP"+p]!= undefined){
    contextMenu.addItem( response.data[largo]["OP"+p][0]+" "+response.data[largo]["OP"+p][1], function(){console.log("HOLA")})
    p=p+1
  }
  //guardo el menu contextoal
  arrContext.push(contextMenu)
}  

function crearBoundariesParaMenuesContextuales(largo,arrbonds,long){
  //obtengo los bordes del highlighter y los guardo
  Boundaries = document.querySelectorAll('.regla'+largo)[0].getBoundingClientRect();
  arrbonds.push(Boundaries)
  //por cada click detecho llamo a una funcion que previene el menu contextual clasico
  //ademas de asignarle la funcion localizar para abrir el menu contextual
  ep.addEventListener('contextmenu', function(e) {
    e.preventDefault()
    i=0
    //si se abrio el menu rompe este while para seguir con la ejecucion normal
    while (i<(long+1)){ if (localizar(e,arrbonds,i)) {break} ;i=i+1}
    
  });
}
//la funcion localizar se fija si el "click" esta dentro del elemento highlited
//si lo esta abre el menu sino cierra y chau
  function localizar(e,arrbonds,largo){
    var x = e.clientX;
        var y = e.clientY;
        var insideX = x >= arrbonds[largo].left && x <= arrbonds[largo].right;
        var insideY = y >= arrbonds[largo].top && y <= arrbonds[largo].bottom;
      
        if(insideX && insideY){
          console.log('On top of "one"!');
          arrContext[largo].openMenu(x,y)
          return true
        }
        else {
          arrContext[largo].closeMenu()
          return false
        }
          
    }
}
