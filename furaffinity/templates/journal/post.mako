<%inherit file="/base.mako" />

% if c.input_errors:
${c.input_errors}<br><br>
% endif

${h.form(h.url(action='post_commit'), method='post', multipart=True)}
<div><label for="title">Title:</label><span>${h.text_field('title', value=c.prefill['title'])}</span></div>
<div><label for="content">Content:</label><span>${h.text_area('content', content=c.prefill['content'])}</span></div>
${h.submit('submit')}
${h.end_form()}

<%def name="title()">Post Journal</%def>

