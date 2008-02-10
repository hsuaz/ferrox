<%inherit file="/base.mako" />

<div class="basic-box">
    <h2>Post Journal</h2>

    % if c.is_edit:
    ${c.form.start(h.url(controller='journal', action='edit_commit', username=c.route['username'], id=c.route['id']), method='post')}
    % else:
    ${c.form.start(h.url(controller='journal', action='post_commit', username=c.route['username']), method='post')}
    % endif
    <dl class="standard-form">
        <dt>Title</dt>
        <dd>${c.form.text_field('title')}</dd>
    </dl>
    <p>${c.form.text_area('content', size="80x10")}</p>
    <p>${c.form.submit('Save')}</p>
    ${c.form.end()}
</div>

<%def name="title()">Post Journal</%def>

