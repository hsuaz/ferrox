function expand_comment(event) {
    var href = event.target.getAttribute('href');
    var note = event.target.parentNode.parentNode.parentNode;
    $.ajax({
        type: 'GET',
        url: href + '/ajax_expand',
        success: function(res) {
            $(note).before(res);
            note.parentNode.removeChild(note);
        },
    });
    event.preventDefault();
}

$(function() {
    $('.js-expand-note').click(expand_comment);
});
