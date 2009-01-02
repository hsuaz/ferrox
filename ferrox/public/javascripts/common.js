var user_request;

function fetch_user_tooltip(event) {
    nuke_user_tooltips();

    var userlink = this;
    var link = $(userlink).find('.js-userlink-target')[0];
    var href = link.href;

    // Temporary 'loading' popup to indicate we're actually doing something
    $(document.body).append('<div class="userlink-popup">loading..</div>');
    position_user_tooltip(userlink);

    user_request = $.ajax({
        type: 'GET',
        url: href + '/ajax_tooltip',
        error: function() {
            user_request = null;
        },
        success: function(res) {
            user_request = null;
            nuke_user_tooltips();
            $(document.body).append(res);
            position_user_tooltip(userlink);
        },
    });
}

// Positions a tooltip relative to a given user link
function position_user_tooltip(userlink_el) {
    var tooltip_el    = $('.userlink-popup');
    var offset        = $(userlink_el).offset();
    var tooltip_width = tooltip_el.width();
    var body_width    = document.body.offsetWidth;

    tooltip_el.css('top', (offset.top + $(userlink_el).height()) + 'px');
    tooltip_el.css('left', offset.left + 'px');

    // If the tooltip extends past the right margin, shift it left
    if (body_width < offset.left + tooltip_width) {
        // -15 accounts for vertical scrollbar width
        tooltip_el.css('left', (body_width - tooltip_width - 15) + 'px');
    }
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
