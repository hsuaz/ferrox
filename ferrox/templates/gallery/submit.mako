<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div class="basic-box">

    % if c.edit:
    <h2>Editing submission ${c.submission.title}
        % if c.auth_user != c.target_user:
            on behalf of ${lib.user_link(c.target_user)}
        % endif
    </h2>
    ${c.form.start(h.url_for(controller='gallery', action='edit_commit', id=c.submission.id, username=c.submission.primary_artist.username), method='post', multipart=True)}
    % else:
    <h2>Submit Art</h2>
    ${c.form.start(h.url_for(controller='gallery', action='submit_upload', username=c.route['username']), method='post', multipart=True)}
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
        <dd>${c.form.text_area('description', size="80x10")}</dd>
        <dt>Select Avatar:</dt>
        % if c.edit:
        <dd>${lib.avatar_selector(c.submission.primary_artist)}</dd>
        % else:
        <dd>${lib.avatar_selector(c.auth_user)}</dd>
        % endif
    </dl>
    <p> ${c.form.submit('submit')} </p>
    ${c.form.end()}
</div>

<%def name="title()">Submit Art</%def>

