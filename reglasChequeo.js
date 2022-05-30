var ep = document.getElementById('id_texto')
var id='id_texto'
var Boundaries
var contextMenu
var texto=ep.value
var long=0
var arr=[]
var arrContext=[]
var arrbonds=[]
var arrOP=[] // voy a tener siempre una razon, lo que me varian son las opciones
var arrInicio=[]
var arrFin=[]
var arrReemplazo=[]
var largo = 0
var clickActual
window.onload = ()=>{


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
      let largoD= 0
      while (largoD < (long+1)){
        //console.log(response.data.length)
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
      //console.log(arr)
      //console.log("ARREGLOS DE OP")
      //console.log(arrOP)
      //hightlighter
    
      $('#'+id).highlightWithinTextarea({
        highlight: arr
    });
    //console.log("HOLA 3")
    //console.log(response.data[2]["Razon"])
    //MENU CONTEXTUAL

    
    
    while (largo < (long+1)) {
    contextMenu = CtxMenu(document.querySelectorAll('.regla'+largo)[0]);
    //console.log(document.querySelectorAll('.regla'+largo)[0])
    contextMenu.addItem(response.data[largo]["Razon"])
    contextMenu.addSeparator(index = 1)
    p=1
    while(response.data[largo]["OP"+p]!= undefined){
      //console.log(response.data[largo]["OP"+p])
      let reemplazo=response.data[largo]["OP"+p][1]
      contextMenu.addItem( response.data[largo]["OP"+p][0]+" "+response.data[largo]["OP"+p][1],function(){reemplazarTexto(arrbonds,response,reemplazo) })
      p=p+1
    }
    //contextMenu.addItem( response.data[0]["OP1"][0]+" "+response.data[0]["OP1"][1], function(){console.log("HOLA")})
    //contextMenu.addItem( response.data[0]["OP2"][0]+" "+response.data[0]["OP2"][1], function(){console.log("HOLA")})
    
    arrContext.push(contextMenu)
    Boundaries = document.querySelectorAll('.regla'+largo)[0].getBoundingClientRect();
    arrbonds.push(Boundaries)
    //console.log(arrbonds)
    document.getElementById(''+id).addEventListener('contextmenu', function(e) {
      e.preventDefault()
      i=0
      while (i<(long+1)){ if (localizar(e,arrbonds,i)) {break} ;i=i+1}
      
    });
    largo = largo + 1
    }

  });
    //contextMenu = CtxMenu(document.querySelectorAll('.regla')[0]);
    //console.log(document.querySelectorAll('.regla0')[0])
    //contextMenu.addItem(response.data[0]["Razon"])
    //contextMenu.addSeparator(index = 1)
    //contextMenu.addItem( response.data[0]["OP1"][0]+" "+response.data[0]["OP1"][1], function(){console.log("HOLA")})
    //contextMenu.addItem( response.data[0]["OP2"][0]+" "+response.data[0]["OP2"][1], function(){console.log("HOLA")})

    
    document.getElementById(''+id).addEventListener('click', function(e){e.preventDefault();
      q=0 
      while(q<=long){arrContext[q].closeMenu();q= q + 1}
      
      });
  



  function localizar(e,arrbonds,largo){
        var x = e.clientX;
        var y = e.clientY;
        var insideX = x >= arrbonds[largo].left && x <= arrbonds[largo].right;
        var insideY = y >= arrbonds[largo].top && y <= arrbonds[largo].bottom;
      
        if(insideX && insideY){
          console.log('On top of "one"!');
          this.clickActual=[x,y]
          arrContext[largo].openMenu(x,y)
          return true
        }
        else {
          arrContext[largo].closeMenu()
          return false
        }
          
    }
}
function reemplazarTexto(arrbonds,response,text){
 act=0
 target=document.getElementById(id).value
 while(arrbonds[act]!= undefined){
  var insideX = clickActual[0] >= arrbonds[act].left && clickActual[0] <= arrbonds[act].right;
  var insideY = clickActual[1] >= arrbonds[act].top && clickActual[1] <= arrbonds[act].bottom;
   if(insideX && insideY){
     break;
   }
   act=act+1
 }
 let ini
 let fin
 ini= response.data[act]["OP1"][2]
 fin= response.data[act]["OP1"][3]
var firstPart = target.substr(0,ini); // "this is "
var lastPart = target.substr(fin);
target=firstPart+text+lastPart
console.log(target)
document.getElementById(id).value=target
}