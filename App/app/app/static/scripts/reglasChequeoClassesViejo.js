
export default class Campo {
    constructor(id,sep,tipo,fieldsCorrelativas){
        //console.log(sep)
        this.campo = id
        this.fieldHerrmanas=fieldsCorrelativas
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
        this.textoActual
        this.datosFiltroActual
        this.noEsReemplazo=true
        this.reemplazoDesdeHasta=[]

    }
funcionBuscarRangoDeCambio(texto){
    let aux1=-1
    let aux2=99999
    let diferencia= texto.length - this.textoActual
    if (this.textoActual==undefined){
        this.reemplazoDesdeHasta=[0,0]
    }
    let i=0
    while(i<texto.length){
        if(this.textoActual[i]!=texto[i]){
            if (this.textoActual[i+diferencia]!=texto[i]){aux1=Math.max(aux1,i); console.log(i)}
            //un aproach interesante: conocer el primer cambio mas cercano a la posicion 0
            //cortar el string original en esa posicion junto con el modificado
            //volver a buscar el siguiente string modificado de la nueva posicion del 0 y guardarlo en una var
            //volver a repetir el mismo proc. si se encontro otro nuevo modificacion mas cercano a  cortar y actualizar la var.
            //repetir 
            
            aux2=Math.min(aux2,i)
        }
        i=i+1
    }
    let z=""
    i=aux2
    console.log(aux1,aux2)
    while(i<aux1+1){
        z=z+texto[i]
        i=i+1
    }
    console.log(z)
}
chequeoDeCambios(texto){
    if (texto == this.textoActual){
        //console.log("ES IGUAL " + this.campo)
        return true
    }
    else {
        //console.log("CAMBIO "+ this.campo)
        if (this.textoActual==undefined){ this.textoActual=texto}
        return false
    }
}
siCambioLaRegla(arr1,arr2){
    let i=0
    if (arr1==undefined)
    {   this.datosFiltroActual=arr2.map((x) => x) //duplico
        return true
    }
    for(i=0;i<this.long+1;i++){
        if (JSON.stringify(arr1[i])!=JSON.stringify(arr2[i])){
            return true
        }
    }
    return false
}
pedirDatosActualizar(){
   
   return this.pedirDatos()
}
datosEspecificos(){
    if (this.tip == "Scenario"){
        let i=0
        let fieldsHer={}
        while (i< this.fieldHerrmanas.length){
            fieldsHer[this.fieldHerrmanas[i]]=(document.getElementById(this.fieldHerrmanas[i]).value)
            i = i+1
        }
        return fieldsHer
    }
}
pedirDatos(){
    let datosAdicionales=this.datosEspecificos()
    if (this.chequeoDeCambios(document.getElementById(this.campo).value)&&this.noEsReemplazo){
        return false
    }
    
    //console.log("PIDE")
    //'http://localhost:5000/passive_voice'
    //http://localhost:5000/spelling
    //http://apirequesem-requirements-healer.okd.lifia.info.unlp.edu.ar/reglas

    axios.post('http://apirequesem-requirements-healer.okd.lifia.info.unlp.edu.ar/spelling', 
    {
        texto:document.getElementById(this.campo).value,
        tipo:this.tip,
        adicional:JSON.stringify(datosAdicionales),
        yoSoy:this.campo,
    }
).then(
        res=>{console.log(res);
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
        this.long= this.datosFiltro.length - 1
        if(this.siCambioLaRegla(this.datosFiltroActual,this.datosFiltro)){
            this.arr=[]
            this.arrContext=[]
            this.arrbonds=[]
            this.datosFiltroActual=this.datosFiltro.map((x) => x)
        }
        if(!this.noEsReemplazo){
            this.arrbonds=[]
        }
        this.highlighterConfigurar(this.datosFiltro)
        this.menuConfigurar(res)
        let stateCheck = setInterval(() => {
            if (document.readyState === 'complete') {
              clearInterval(stateCheck);
              this.actualizarBoundings()
            }
          }, 100);
        }
    )
}
actualizarBoundings(){
    //hace un bugFix cuando carga el doc :D
    let i = 0
    this.arrbonds=[]
    while(i<(this.long + 1)){
        this.arrbonds.push(document.querySelectorAll('.regla'+(i+this.delta))[0].getBoundingClientRect())
        i = i+1
    }
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
        
        //this.actualizarBoundings()
        }
        
}
//SALVO ESTE QUE SIRVE PARA AYUDAR AL REEMPLAZAR
teVasAEnterarX3(reemplazo,response){
    return (e)=>{
        var aux=""
        aux=Campo.reemplazarTexto(this.arrbonds,response,reemplazo,document.getElementById(this.campo).value,this.clickActual)
        document.getElementById(this.campo).value=aux
        $('#'+this.campo).highlightWithinTextarea('destroy');
        this.datosFiltroActual=undefined
        this.noEsReemplazo=false
        this.textoActual=aux
        this.pedirDatos()
        }
}

highlighterConfigurar(response){
    let largoD= 0
    //console.log("ACA HOLA!")
    //console.log(response)
    while (largoD < (this.long+1)){
        if (response[largoD]["tipo"]=="general" || response[largoD]["tipo"]==this.tip){
            //console.log(response[largoD]["OP1"][2]+","+response[largoD]["OP1"][3])
            this.arr.push({highlight: [response[largoD]["OP1"][2], response[largoD]["OP1"][3]],
            className: 'regla'+(largoD+this.delta)})  
        }
            
        largoD = largoD + 1
      }
      $('#'+this.campo).highlightWithinTextarea({
        highlight: this.arr
      });
      this.noEsReemplazo=true
}
menuConfigurar(response){
    let largo=0
    while (largo < (this.long+1)) {
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
    //console.log(y)
    //console.log(x)
    //console.log("CHEQUEO")
    //console.log("coord X: "+ arrbonds[largo].left + "<X:"+x+"<"+arrbonds[largo].right)
    //console.log("coord Y: "+ arrbonds[largo].top + "<y:"+y+"<"+arrbonds[largo].bottom)
    var insideX = x >= arrbonds[largo].left && x <= arrbonds[largo].right;
    var insideY = y >= arrbonds[largo].top && y <= arrbonds[largo].bottom;
    //console.log("inside x: "+insideX)
    //console.log("inside y: "+insideY)
    if(insideX && insideY){
      console.log('On top of "one"!');
      this.clickActual=[x,y]
      this.teVasAEnterarX2(this.long)
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
   return target
   }





}




