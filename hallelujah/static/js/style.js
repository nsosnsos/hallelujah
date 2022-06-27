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

