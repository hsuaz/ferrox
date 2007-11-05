<%inherit file="../base.mako" />

<div id="news_page">
    <span>Post News</span>
    ${h.form(h.url(controller='news', action='do_post'), method='post')}
    <div>
        <label for="title">Headline:</label>
        <span>${h.text_field('title')}</span>
    </div>
    <div>
        <label for="title">Content:</label><br>
        <span>${h.text_area('content')}</span>
    </div>
    ${h.submit('Post')}
    ${h.end_form()}

</div>

<%def name="title()">Post News</%def>

