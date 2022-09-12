export default class AlertasDeReglas{
    constructor(id,tipo){
        //console.log(sep)
        this.campo = id
        this.tip=tipo
    }
buscarLinea(texto,pos1,pos2){
    let inicio_oracion = 0
    let linea = 1
    let punto = -1//donde termina la oracion
    let i=0
    while (i != texto.length){
        if (texto[i] == ".") {
            //encontre el punto
            punto = i
            //pregunto si la posicion esta antes del punto y despues del  inicio de oracion
            if ((pos1 >= inicio_oracion) && (pos2 <= punto)){
                return linea
            }
            else {
                linea = linea + 1
                inicio_oracion = punto + 1
                punto = -1
            }
        }
        i= i + 1
    }
    //si no encontro el punto devuelvo la linea igual. en el peor de los casos es linea 1 no enchufo un punto
    return linea
}
devolverLineasAfectadas(res){
    let desc=""
    let x = 0
    let lista = new Set()
    while (res.data[x]!=undefined){
        lista.add(this.buscarLinea(document.getElementById(this.campo).value,res.data[x]["OP1"][2],res.data[x]["OP1"][3]))
        x= x + 1
    }
    for (let item of lista) desc = desc + item+" "
    return desc
}
ejecutar(){


axios.post('http://localhost:5000/one_verb', 
{
    data:document.getElementById(this.campo).value,
}
).then(

res=>{ 
    const element = document.getElementById("advertencias");
    if (res.data.length !=0){
        let para = document.createElement("h5");
        let node = document.createTextNode("Exceso de verbos en "+this.campo.slice(3,-1)+", en linea/as "+this.devolverLineasAfectadas(res)+" se recomienda eliminar verbos");
        para.appendChild(node);
        element.appendChild(para);
    }
    else{
        while(element.firstChild){
            element.removeChild(element.firstChild)
        }
    }

})

axios.post('http://localhost:5000/null_subject', 
{
    data:document.getElementById(this.campo).value,
}
).then(

res=>{ 
    const element = document.getElementById("advertencias");
    if (res.data.length !=0){
        let para = document.createElement("h5");
        let node = document.createTextNode("No hay sujeto en "+this.campo.slice(3,-1));
        para.appendChild(node);
        element.appendChild(para);
    }
    else{
        while(element.firstChild){
            element.removeChild(element.firstChild)
        }
    }
    
})
axios.post('http://localhost:5000/passive_voice', 
{
    data:document.getElementById(this.campo).value,
}
).then(

res=>{ 
    const element = document.getElementById("advertencias");
    if (res.data.length !=0){
        let para = document.createElement("h5");
        let node = document.createTextNode("Existe una oracion con adjetivos o adverbios en "+this.campo.slice(3,-1)+", en linea/as "+this.devolverLineasAfectadas(res));
        para.appendChild(node);
        element.appendChild(para);
    }
    else{
        while(element.firstChild){
            element.removeChild(element.firstChild)
        }
    }
    
})
axios.post('http://localhost:5000/adj_and_adv', 
{
    data:document.getElementById(this.campo).value,
}
).then(

res=>{ 
    const element = document.getElementById("advertencias");
    if (res.data.length !=0){
        let para = document.createElement("h5");
        let node = document.createTextNode("Existe una oracion en voz pasiva en "+this.campo.slice(3,-1)+"en linea/as "+this.devolverLineasAfectadas(res));
        para.appendChild(node);
        element.appendChild(para);
    }
    else{
        while(element.firstChild){
            element.removeChild(element.firstChild)
        }
    }
    
})

}
ejecutarLimpieza(){
    const element = document.getElementById("advertencias");
    while(element.firstChild){
        element.removeChild(element.firstChild)
    }
    
    }
}
