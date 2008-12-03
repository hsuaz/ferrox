function find_details(event)
{
    var e = event.target
    while ( e.className != 'submission' )
    {
        e = e.parentNode;
    }
    e = e.childNodes[1];
    return e;
}
function hide_details(event)
{
    var e = find_details(event);
    $(e).hide();
}
function show_details(event)
{
    var e = find_details(event);
    $(e).show();
}

$(function() {
    $('li').filter('.submission').hover(show_details, hide_details);
});
