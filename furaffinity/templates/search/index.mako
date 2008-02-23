<%inherit file="/base.mako" />

<div class="basic-box">
    <h2>Post Journal</h2>
    % if c.input_errors:
    <p>${c.input_errors}</p>
    % endif

    ${c.form.start(h.url(controller='search', action='do'), method='post')}
    <dl class="standard-form">
        <dt>Query:</dt>
        <dd>${c.form.text_field('query_main')}</dd>
        <dt>Search What:</dt>
        <dd>${c.form.check_box('search_title', checked=True)} Title 
        ${c.form.check_box('search_description', checked=True)} Description </dd>
        <dt>Search For:</dt>
        <dd>${h.radio_button('search_for', value='submissions', checked='checked')} Submissions 
        ${h.radio_button('search_for', value='journals')} Journals
        <dt>Tags:</dt>
        <dd>${c.form.text_field('query_tags')}</dd>
        <dt>Artist/Author:</dt>
        <dd>${c.form.text_field('query_author')}</dd>
    </dl>
    
    <p>${c.form.submit('Search')}</p>
    ${c.form.end()}
</div>

<%def name="title()">Search</%def>
