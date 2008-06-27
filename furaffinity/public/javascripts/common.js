var user_request;

function fetch_user_tooltip(event) {
    nuke_user_tooltips();

    var userlink = this;
    var link = $(userlink).find('.js-userlink-target')[0];
    var href = link.href;

    // Temporary 'loading' popup to indicate we're actually doing something
    $(userlink).append('<div class="userlink-popup">loading..</div>');

    user_request = $.ajax({
        type: 'GET',
        url: href + '/ajax_tooltip',
        error: function() {
            user_request = null;
        },
        success: function(res) {
            $(userlink).find('.userlink-popup').remove();
            $(userlink).append(res);
            var tooltip_j = $(userlink).find('.userlink-popup');

            var right_edge = tooltip_j.offset().left + tooltip_j.width();
            var body_width = document.body.offsetWidth;
            if (right_edge > body_width) {
                tooltip_j.css('left', (body_width - right_edge - 15) + 'px');
            }
        },
    });
}

// Called to abort any and all tooltip requests and remove any existing
// tooltips from the page.
function nuke_user_tooltips() {
    if (user_request) {
        user_request.abort();
        user_request = null;
    }

    $('.userlink-popup').remove();
}

$(function() {
    $('.userlink').hover(fetch_user_tooltip, nuke_user_tooltips);
});
