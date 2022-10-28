/* flash animation */
window.setTimeout(function () {
    $(".alert").fadeTo(500, 0).slideUp(500, function () {
        $(this).remove();
    });
}, 2000);

/* theme toggle */
$("#toggle").change(function() {
    $("#toggleForm").submit();
});

/* load css to end of head */
function loadcssfile(filename) {
    var head = document.getElementsByTagName('head')[0];
    var link = document.createElement('link');
    link.setAttribute('rel', 'stylesheet');
    link.setAttribute('type', 'text/css');
    link.setAttribute('href', filename);
    head.appendChild(link);
}

