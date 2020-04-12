# dynamic loading data when scrolling down to bottom of page
$(window).scroll(() => {
  var cur_y = $(window).scrollTop();
  var window_height = $(window).height();
  var document_height = $(document).height();
  if (cur_y + window_height == document_height) {

  }

  function load_blog(index, limit) {
    $.get('/api?index=' + index + '&limit=' + limit, (data) => {

    });
  }
});