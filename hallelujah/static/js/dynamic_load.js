function load_data(fetch_url, data_div, sentinel, limit) {
    fetch(fetch_url).then(response => response.json()).then(data => {
        offset += data.length;
        if (!data.length || data.length < limit) {
            sentinel.innerHTML = '<div class="text-muted">No more articles.</div>';
            intersectionObserver.unobserve(sentinel);
        }

        for (var index = 0; index < data.length; index++) {
            var page = `
                <div class="card mb-5">
                    <div class="card-header">
                        <h5><a href="` + data[index].url + `" class="stretched-link">` + data[index].title +`</a></h5>
                    </div>
                    <div class="card-body">
                        ` + data[index].truncated_content + `
                    </div>
                    <div class="card-footer d-flex justify-content-between text-muted">
                        <div>` + data[index].author + `</div>
                        <div>` + moment(data[index].timestamp).format('YYYY-MM-DD HH:mm:ss') + `</div>
                    </div>
                </div>`;
            $('#data_div').append(page);
        }
    });
}

