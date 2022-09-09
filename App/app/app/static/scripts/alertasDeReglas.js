export default class AlertasDeReglas{
    constructor(id,tipo){
        //console.log(sep)
        this.campo = id
        this.tip=tipo
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
        let node = document.createTextNode("Exceso de verbos en "+this.campo.slice(3,-1)+" se recomienda eliminar verbos");
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
        let node = document.createTextNode("Existe una oracion con adjetivos o adverbios en "+this.campo.slice(3,-1));
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
        let node = document.createTextNode("Existe una oracion en voz pasiva en "+this.campo.slice(3,-1));
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
