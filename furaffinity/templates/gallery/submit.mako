<%inherit file="base.mako" />

<div class="basic-box">
    <h2>Submit Art</h2>

    % if c.edit:
    ${c.form.start(h.url(controller='gallery', action='edit_commit', id=c.submission.id, username=c.submission.primary_artist.username), method='post', multipart=True)}
    % else:
    ${c.form.start(h.url(controller='gallery', action='submit_upload'), method='post', multipart=True)}
    % endif

    <dl class="standard-form">
        <dt>File</dt>
        <dd>${c.form.file_field('fullfile')}</dd>
        <dt>Half-view</dt>
        <dd>${c.form.file_field('halffile')}</dd>
        <dt>Thumbnail</dt>
        <dd>${c.form.file_field('thumbfile')}</dd>
        <dt>Title</dt>
        <dd>${c.form.text_field('title')}</dd>
        <dt>Tags</dt>
        <dd>${c.form.text_field('tags')}</dd>
        <dt>Description</dt>
        <dd>${h.text_area('description', size="80x10")}</dd>
    </dl>
    <p> ${c.form.submit('submit')} </p>
    ${c.form.end()}
</div>

<%def name="title()">Submit Art</%def>

