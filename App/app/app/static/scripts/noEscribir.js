//var myField= document.getElementById("id_texto").readOnly = true;
//Para desacticar los inputs!
//var myField1= document.getElementById("id_Goal").readOnly = true;
//var myField2= document.getElementById("id_Context").readOnly = true;
//v/ar myField3= document.getElementById("id_Resources").readOnly = true;
//var myField4= document.getElementById("id_Actors").readOnly = true;
//var myField5= document.getElementById("id_Episodes").readOnly = true;
var fields = JSON.parse(document.getElementById('fields').textContent);
let i=0
let z
console.log(fields[i])
while(i<fields.length){
    z=document.getElementById(fields[i]).readOnly = true;
    i=i+1
}