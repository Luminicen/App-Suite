
        bkLib.onDomLoaded(function() { nicEditors.allTextAreas() }); // this method will transform all textares to rich text editors
 var ok
        bkLib.onDomLoaded(function() {
            ok=new nicEditor().panelInstance('txtAboutMe');
            console.log(ok)
        }); // this will transform textarea with id txt only
 
        bkLib.onDomLoaded(function() {
             new nicEditor({fullPanel : true}).panelInstance('area2');
        }); // convert text area with id txt2 to rich text editor with all options.
