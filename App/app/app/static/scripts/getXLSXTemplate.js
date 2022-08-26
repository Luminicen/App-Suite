
document.getElementById("botonTemplate").onclick = function() {myFunction()};

function myFunction() {
    axios({
        url: 'https://guarded-falls-24810.herokuapp.com/template', 
        method: 'GET',
        responseType: 'blob', 
    }).then((response) => {
        console.log("XDD")
        console.log(response)
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'template.xlsx'); 
        document.body.appendChild(link);
        link.click();
    });
    console.log("XDD")
}