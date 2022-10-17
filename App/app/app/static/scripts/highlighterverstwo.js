export default class CampoV2{
    constructor(id,delta,tipo,otrosCampos){
        this.id_campo=id
        this.tipo_campo=tipo
        this.otrosCampos=otrosCampos
        this.arr=[] // para el highlighter
        this.delta=delta // variable para la corrida de scroll
        this.boundaries=[]//para los bondaries
        this.boundariesLenght = -1
        this.booleanosBoundaries=[] //para marcar si es accesible o no el ctx
        this.arrContextualMenu=[]
    }
    pedirDatos(){
        axios.post('http://127.0.0.1:5000/dict', 
    {   
        //Datos que le mando a la api para procesamiento
        data:document.getElementById(this.id_campo).value,
        tipo:this.tipo_campo,
        adicional:JSON.stringify(this.otrosCampos),
        yoSoy:this.id_campo,
    }
).then(
        res=>{
            let aux
            aux=res.data
            console.log(res);
            aux=res.data
            this.highlighterConfigurar(aux)
            this.menuContextualConfigurar(aux)
        }
    )

    

    
    }

    highlighterConfigurar(response){
        //La api va a ser la encargada de ver los tipos, aca en el highlighter
        //recibo un intervalo x y lo marco en el texto
        //casos a considerar: 
        //actualizacion del highlight cuando escribe ya sea borrar o agregar data
        //  si se borra:
        //      dentro del intervalo marcado --> F volver a pedir o deselect
        //      si es fuera del intervalo --> correr highlight
        //  si se agrega info:
        //      dentro del intervalo marcado --> F volver a pedir o deselect
        //      si es fuera del intervalo --> correr highlight
        //superposicion de highlights
        //  se debe tomar en cuenta cuando se reciben los datos directamente
        let largoTotal= response.data.length - 1
        this.boundariesLenght = response.data.length - 1
        let largoD=0
        while (largoD <= (largoTotal)){
            this.arr.push(
            {
                highlight: response.data[largoD]["marcar"],
                className: 'regla'+(largoD+this.delta)
            })  
            largoD = largoD + 1
        }
        console.log(this.arr)
          $('#'+this.id_campo).highlightWithinTextarea({
            highlight: this.arr
          });
          

        }
        menuContextualConfigurar(response){
            let inicio = 0
            let final = response.data.length 
            let bound
            let menu
            while(inicio < final){
                //try{
                bound=document.querySelectorAll('.regla'+(inicio+this.delta))[0].getBoundingClientRect()
                this.boundaries.push(bound)
                this.booleanosBoundaries.push(true)
                menu = CtxMenu(document.querySelectorAll('.regla'+(inicio+this.delta))[0]);
                menu.addItem(response.data[inicio]["Razon"])
                let index = 1
                menu.addSeparator(index = 1)
                let p=1
                while(response.data[inicio]["OP"+p]!= undefined){
                    let reemplazo=response.data[inicio]["OP"+p][1]
                    menu.addItem( response.data[inicio]["OP"+p][0]+" "+response.data[inicio]["OP"+p][1],console.log("HOLA") )
                    p=p+1
                }
                this.arrContextualMenu.push(menu)
            //}
                //catch{console.log("ERROR")}
                inicio = inicio +1
            }
            console.log(this.boundaries)
            document.addEventListener('scroll', this.actualizarBoundaries);
            const areaX = document.getElementById(this.id_campo)
            areaX.addEventListener('keydown',(e) => {
                this.actualizarBoundaries()
            })
            areaX.addEventListener('contextmenu', (e)=>{
                e.preventDefault()
                let i=0
                this.actualizarBoundaries()
                while (i<=(this.boundariesLenght)){
                    if (this.localizar(e,this.boundaries,i)) {break} ;
                    i=i+1
                }
                });
            areaX.addEventListener('click', (e)=>{
                e.preventDefault()
                this.cerrarMenues(this.boundariesLenght)
            });
        }
        actualizarBoundaries(){
            let recorro=0
            let max = this.boundariesLenght
            while (recorro <= max){
                this.booleanosBoundaries[recorro]=true
                try{
                this.boundaries[recorro]=document.querySelectorAll('.regla'+(recorro+this.delta))[0].getBoundingClientRect();}
                catch{this.booleanosBoundaries[recorro]=false}
                recorro = recorro + 1
            }
            try{this.cerrarMenues(max)}catch{}
        }
        localizar(e,arrbonds,posicionArreglo){
            var x = e.clientX ;
            var y = e.clientY ;
            var insideX = x >= arrbonds[posicionArreglo].left && x <= arrbonds[posicionArreglo].right;
            var insideY = y >= arrbonds[posicionArreglo].top && y <= arrbonds[posicionArreglo].bottom;
            if(insideX && insideY && this.booleanosBoundaries[posicionArreglo]){
              console.log('On top of "one"!');
              //this.clickActual=[x,y]
              //this.teVasAEnterarX2(this.long)
              console.log(x,y)
              this.arrContextualMenu[posicionArreglo].openMenu(x + window.scrollX,y + window.scrollY)
              return true
            }
            else {
              
              this.arrContextualMenu[posicionArreglo].closeMenu()
              console.log("FALLO")
              console.log(x,y)
              console.log(arrbonds[posicionArreglo])
              return false
            }
              
        }
        cerrarMenues(long){
            let q=0 
            while(q<=long){this.arrContextualMenu[q].closeMenu();q= q + 1}
        }

    //fin de clase
}

