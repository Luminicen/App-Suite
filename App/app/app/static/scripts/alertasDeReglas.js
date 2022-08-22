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

}
ejecutarActualizacion(){


    axios.post('http://localhost:5000/one_verb', 
    {
        data:document.getElementById(this.campo).value,
    }
    ).then(
    
    res=>{ 
        const element = document.getElementById("advertencias");
        while(element.firstChild){
            element.removeChild(element.firstChild)
        }
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
    
    }
}
