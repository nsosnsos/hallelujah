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

/* data content adaption */
function data_container_adaption() {
    header = document.querySelector("header");
    footer = document.querySelector("footer");
    data_container = document.querySelector("#data_container");
    header_style = getComputedStyle(header);
    footer_style = getComputedStyle(footer);
    header_height = header.clientHeight + parseInt(header_style.marginTop) + parseInt(header_style.marginBottom);
    footer_height = footer.clientHeight + parseInt(footer_style.marginTop) + parseInt(footer_style.marginBottom);
    data_container_height = window.innerHeight - header_height - footer_height;
    data_container.style.minHeight = data_container_height + "px";
}

