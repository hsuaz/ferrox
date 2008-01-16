<%inherit file="base.mako" />

% if c.input_errors:
<p>${c.input_errors}</p>
% endif

<div class="basic-box">
    <h2>Submit Art</h2>

    % if c.edit:
    ${h.form(h.url(controller='gallery', action='edit_commit', id=c.submission.id), method='post', multipart=True)}
    % else:
    ${h.form(h.url(controller='gallery', action='submit_upload'), method='post', multipart=True)}
    % endif

    <dl class="standard-form">
        <dt>File</dt>
        <dd>${h.file_field('fullfile')}</dd>
        <dt>Half-view</dt>
        <dd>${h.file_field('halffile')}</dd>
        <dt>Thumbnail</dt>
        <dd>${h.file_field('thumbfile')}</dd>
        <dt>Title</dt>
        <dd>${h.text_field('title', value=c.prefill['title'])}</dd>
    </dl>
    <p> Description: </p>
    <p> ${h.text_area('description', size="80x10", content=c.prefill['description'])} </p>
    <p> ${h.submit('submit')} </p>
    ${h.end_form()}
</div>

<%def name="title()">Submit Art</%def>

