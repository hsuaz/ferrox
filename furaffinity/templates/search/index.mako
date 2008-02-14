<%inherit file="/base.mako" />

<div class="basic-box">
    <h2>Post Journal</h2>
    % if c.input_errors:
    <p>${c.input_errors}</p>
    % endif

    ${h.form(h.url(controller='search', action='do'), method='post')}
    <dl class="standard-form">
        <dt>Query:</dt>
        <dd>${h.text_field('query_main')}</dd>
    </dl>
    <dl class="standard-form">
        <dt>Search What:</dt>
        <dd>${h.check_box('search_title', checked=True)} Title 
        ${h.check_box('search_description', checked=True)} Description </dd>
    </dl>
    <dl class="standard-form">
        <dt>Search For:</dt>
        <dd>${h.radio_button('search_for', value='submissions')} Submissions 
        ${h.radio_button('search_for', value='journals')} Journals
        ${h.radio_button('search_for', value='news')} News</dd>
    </dl>
    <dl class="standard-form">
        <dt>Tags:</dt>
        <dd>${h.text_field('query_tags')}</dd>
    </dl>
    <dl class="standard-form">
        <dt>Artist/Author:</dt>
        <dd>${h.text_field('query_author')}</dd>
    </dl>
    
    <p>${h.submit('Search')}</p>
    ${h.end_form()}
</div>

<%def name="title()">Search</%def>

