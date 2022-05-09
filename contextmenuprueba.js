var selectedText;
$("#txtAboutMe").bind("contextmenu", function(event) {

  // Avoid the real one
  event.preventDefault();
  //alert(getSelectionText());
  selectedText = getSelectionText();
  $("[data-action='first']").text('Search Bing for "'+selectedText+'"');
  $("[data-action='second']").text('Search Google for "'+selectedText+'"');
  $("[data-action='third']").text('Search Yahoo for "'+selectedText+'"');
  // Show contextmenu
  $(".custom-menu").finish().toggle(100).

  // In the right position (the mouse)
  css({
    top: event.pageY + "px",
    left: event.pageX + "px"
  });
});

// If the document is clicked somewhere
$(document).bind("mousedown", function(e) {

  // If the clicked element is not the menu
  if (!$(e.target).parents(".custom-menu").length > 0) {

    // Hide it
    $(".custom-menu").hide(100);
  }
});

// If the menu element is clicked
$(".custom-menu li").click(function() {

  // This is the triggered action name
  switch ($(this).attr("data-action")) {

    // A case for each action. Your actions here
    case "first":
       window.open('http://www.bing.com/search?q='+selectedText, '_blank');
      break;
    case "second":
       window.open('https://www.google.com/search?q='+selectedText, '_blank');
      break;
    case "third":
       window.open('https://search.yahoo.com/search?p='+selectedText, '_blank');
      break;
  }

  // Hide it AFTER the action was triggered
  $(".custom-menu").hide(100);
});

function getSelectionText() {
  var text = "";
  var activeEl = document.activeElement;
  var activeElTagName = activeEl ? activeEl.tagName.toLowerCase() : null;
  if (
    (activeElTagName == "textarea" || activeElTagName == "input") &&
    /^(?:text|search|password|tel|url)$/i.test(activeEl.type) &&
    (typeof activeEl.selectionStart == "number")
  ) {
    text = activeEl.value.slice(activeEl.selectionStart, activeEl.selectionEnd);
  } else if (window.getSelection) {
    text = window.getSelection().toString();
  }
  return text;
}

document.onmouseup = document.onkeyup = document.onselectionchange = function() {
  document.getElementById("sel").value = getSelectionText();
};

$("#btnSelectedText").click(function() {
  alert(getSelectionText());
});