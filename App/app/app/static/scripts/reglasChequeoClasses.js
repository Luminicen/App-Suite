export default class Campo {
    constructor(id,sep,tipo){
        //console.log(sep)
        this.campo = id
        this.delta= sep
        this.tip=tipo
        this.Boundaries
        this.contextMenu
        this.long=0
        this.arr=[]
        this.arrContext=[]
        this.arrbonds = []
        this.largo = 0
        this.clickActual=[]
        this.data={}
        this.datosFiltro=[]
    }
pedirDatosActualizar(){
   this.arr=[]
   this.arrContext=[]
   this.arrbonds=[]
   return this.pedirDatos()
}
pedirDatos(){
    axios.post('http://localhost:5000/passive_voice',{texto:document.getElementById(this.campo).value}).then(
        res=>{//console.log(res);
        this.data=res.data;
        this.long=res.data.length - 1
        let i = 0
        this.datosFiltro=[]
        while (i<this.long + 1){
            if (res.data[i]["tipo"]=="general" || res.data[i]["tipo"]==this.tip){
                this.datosFiltro.push(res.data[i])
            }
            i = i+1
        }
        console.log(this.datosFiltro)
        console.log(this.datosFiltro[0])
        this.long= this.datosFiltro.length - 1
        this.highlighterConfigurar(this.datosFiltro)
        this.menuConfigurar(res)
        //console.log(this.delta)
        }
    )
}
setText(text){
    this.texto=text
}
//LOS TE VAS A ENTERAR SOLUCIONAN EL PROBLEMA DE PASAR PARAMETROS AL ADD LISTEENER
teVasAEnterar(long){
    return (e)=>{
    e.preventDefault()
        let i=0
        while (i<(this.long+1)){
            if (this.localizar(e,this.arrbonds,i)) {break} ;
                i=i+1
            }
    }
}
teVasAEnterarX2(long){
    return (e)=>{
        e.preventDefault()
        let q=0 
        while(q<=this.long){this.arrContext[q].closeMenu();q= q + 1}
        }
}
//SALVO ESTE QUE SIRVE PARA AYUDAR AL REEMPLAZAR
teVasAEnterarX3(reemplazo,response){
    return (e)=>{
        var aux=""
        aux=Campo.reemplazarTexto(this.arrbonds,response,reemplazo,document.getElementById(this.campo).value,this.clickActual)
        document.getElementById(this.campo).value=aux
        $('#'+this.campo).highlightWithinTextarea('destroy');
        this.arr=[]
        this.arrContext=[]
        this.arrbonds=[]
        this.pedirDatos()
        }
}

highlighterConfigurar(response){
    console.log("CONSOLA")
    console.log(response[0]["OP1"])
    let largoD= 0
    while (largoD < (this.long+1)){
        console.log(response[largoD])
        if (response[largoD]["tipo"]=="general" || response[largoD]["tipo"]==this.tip){
            this.arr.push({highlight: [response[largoD]["OP1"][2], response[largoD]["OP1"][3]],
            className: 'regla'+(largoD+this.delta)})  
        }
            
        largoD = largoD + 1
      }
      $('#'+this.campo).highlightWithinTextarea({
        highlight: this.arr
      });
      
}
menuConfigurar(response){
    let largo=0
    while (largo < (this.long+1)) {
        //console.log(this.delta)
        //console.log(largo+this.delta)
        //console.log('.regla'+(largo+this.delta))
        //console.log(largo)
        this.contextMenu = CtxMenu(document.querySelectorAll('.regla'+(largo+this.delta))[0]);
        this.contextMenu.addItem(response.data[largo]["Razon"])
        let index = 1
        this.contextMenu.addSeparator(index = 1)
        let p=1
        while(response.data[largo]["OP"+p]!= undefined){
          let reemplazo=response.data[largo]["OP"+p][1]
          this.contextMenu.addItem( response.data[largo]["OP"+p][0]+" "+response.data[largo]["OP"+p][1],this.teVasAEnterarX3(reemplazo,response) )
          p=p+1
        }
    
        this.arrContext.push(this.contextMenu)
        this.Boundaries = document.querySelectorAll('.regla'+(largo+this.delta))[0].getBoundingClientRect();
        this.arrbonds.push(this.Boundaries)
        largo = largo + 1
        }
        
        document.getElementById(''+this.campo).addEventListener('contextmenu', this.teVasAEnterar(this.long));
        document.getElementById(''+this.campo).addEventListener('click', this.teVasAEnterarX2(this.long));
}
localizar(e,arrbonds,largo){
    var x = e.clientX + window.scrollX;
    var y = e.clientY + window.scrollY;
    console.log(y)
    console.log(x)
    console.log("CHEQUEO")
    console.log("coord X: "+ arrbonds[largo].left + "<X:"+x+"<"+arrbonds[largo].right)
    console.log("coord Y: "+ arrbonds[largo].top + "<y:"+y+"<"+arrbonds[largo].bottom)
    var insideX = x >= arrbonds[largo].left && x <= arrbonds[largo].right;
    var insideY = y >= arrbonds[largo].top && y <= arrbonds[largo].bottom;
    if(insideX && insideY){
      console.log('On top of "one"!');
      this.clickActual=[x,y]
      this.arrContext[largo].openMenu(x,y)
      return true
    }
    else {
      this.arrContext[largo].closeMenu()
      return false
    }
      
}
static reemplazarTexto(arrbonds,response,text,target,clickActual){
    let act=0
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
   var firstPart = target.toString().substr(0,ini); 
   var lastPart = target.toString().substr(fin);
   target=firstPart+text+lastPart
   //console.log(target)
   this.arr=[]
   this.arrContext=[]
   this.arrbonds=[]
   return target
   }





}




