<%inherit file="/base.mako" />

<div class="basic-box">
    <h2>Post Journal</h2>
    % if c.input_errors:
    <p>${c.input_errors}</p>
    % endif

    % if c.edit:
    ${h.form(h.url(controller='journal', action='edit_commit', username=c.route['username'], id=c.route['id']), method='post')}
    % else:
    ${h.form(h.url(controller='journal', action='post_commit', username=c.route['username']), method='post')}
    % endif
    <dl class="standard-form">
        <dt>Title</dt>
        <dd>${h.text_field('title', value=c.prefill['title'])}</dd>
    </dl>
    <p>${h.text_area('content', size="80x10", content=c.prefill['content'])}</p>
    <p>${h.submit('Save')}</p>
    ${h.end_form()}
</div>

<%def name="title()">Post Journal</%def>

