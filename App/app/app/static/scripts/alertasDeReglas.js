export default class AlertasDeReglas{
    constructor(id,tipo){
        //console.log(sep)
        this.campo = id
        this.tip=tipo
    }

ejecutar(){


axios.post('http://apirequesem-requirements-healer.okd.lifia.info.unlp.edu.ar/api', 
{
    data:document.getElementById(this.campo).value,
}
).then(

res=>{ 

    const element = document.getElementById("advertencias");
    if (res.data["has_more_verb"].length !=0){
        console.log(res.data)
        let para = document.createElement("h5");
        let node = document.createTextNode("Excess of verbs in the field "+this.campo.slice(3,-1)+", in the sentence/s "+obtenerOraciones("has_more_verb",res)+". It is recommended to split the sentence");
        para.appendChild(node);
        element.appendChild(para);
    }
    if (res.data["null_subject"].length !=0){ 
        let para = document.createElement("h5");
        let node = document.createTextNode("There is no subject in  : "+this.campo.slice(3,-1)+" in the sentence/s: "+obtenerOraciones("null_subject",res));
        para.appendChild(node);
        element.appendChild(para);
    }
    if (res.data["hasAdjOrAdv"].length !=0){
        let para = document.createElement("h5");
        let node = document.createTextNode("There is a sentence with adjectives or adverbs in the field "+this.campo.slice(3,-1)+", in the sentence/s "+obtenerOraciones("hasAdjOrAdv",res)+". Please consider replace the adjectives and adverbs with new sentences describing them");
        para.appendChild(node);
        element.appendChild(para);
    }
    if (res.data["has_passive_voice"].length !=0){
        
        
        let para = document.createElement("h5");
        let node = document.createTextNode("There is a sentence with passive voice "+this.campo.slice(3,-1)+" in line/s "+obtenerOraciones("has_passive_voice",res));
        para.appendChild(node);
        element.appendChild(para);
    }


})


}
ejecutarLimpieza(){
    const element = document.getElementById("advertencias");

    while(element.firstChild){
        element.removeChild(element.firstChild)
    }
    this.ejecutar()
    
    }

}
function obtenerOraciones(tipo,res){
        let z=0
        let lineas=""
        while(res.data[tipo][z]!= undefined){
            
            lineas= lineas +res.data[tipo][z]["Oracion"]+" "
            z = z + 1
        }
        return lineas  
}
