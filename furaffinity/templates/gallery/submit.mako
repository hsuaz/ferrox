<%inherit file="base.mako" />

% if c.input_errors:
${c.input_errors}<br><br>
% endif

% if c.edit:
${h.form(h.url(controller='gallery', action='edit_commit', username=c.route['username'], id=c.route['id']), method='post', multipart=True)}
% else:
${h.form(h.url(controller='gallery', action='submit_upload', username=c.route['username']), method='post', multipart=True)}
% endif
<div><label for="fullfile">Full View File:</label><span>${h.file_field('fullfile')}</span></div>
<div><label for="thumbfile">Thumbnail File:</label><span>${h.file_field('thumbfile')}</span></div>
<div><label for="type">Submission Type:</label><span>${h.select('type', c.submitoptions)}</span></div>
<div><label for="title">Title:</label><span>${h.text_field('title', value=c.prefill['title'])}</span></div>
<div><label for="description">Description:</label><span>${h.text_area('description', content=c.prefill['description'])}</span></div>
${h.submit('submit')}
${h.end_form()}

<%def name="title()">Submit Art</%def>

