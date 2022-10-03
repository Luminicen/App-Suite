
document.getElementById("botonTemplate").onclick = function() {myFunction()};

function myFunction() {
    console.log()
    axios({
        url: 'http://app-requirements-healer.okd.lifia.info.unlp.edu.ar/template', 
        method: 'GET',
        responseType: 'blob', 
    }).then((response) => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'template.xlsx'); 
        document.body.appendChild(link);
        link.click();
    });
    console.log("XDD")
}