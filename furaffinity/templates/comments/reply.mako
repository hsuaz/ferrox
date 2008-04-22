<%namespace name="lib" file="/lib.mako"/>
<%namespace name="comments" file="/comments/lib.mako"/>
<%inherit file="base.mako" />

<ul class="mini-linkbar">
    <li>${h.link_to("%s Back" % h.image_tag('/images/icons/go-up.png', ''), '/' + c.discussion_url)}</li>
</ul>

% if c.comment:
${comments.comment_tree([c.comment], c.discussion_url)}
% endif

<div class="basic-box">
    <h2>Reply</h2>

    % if 'id' in c.route:
    ${c.form.start(h.url(controller='comments', action='reply_commit', discussion_url=c.discussion_url, id=c.route['id']), method='post')}
    % else:
    ${c.form.start(h.url(controller='comments', action='reply_commit', discussion_url=c.discussion_url), method='post')}
    % endif
    <dl class="standard-form">
        <dt>Subject</dt>
        <dd>${c.form.text_field('subject')}</dd>
        <dt>Message</dt>
        <dd>${c.form.text_area('content', size='80x10')}</dd>
    </dl>
    <p>${c.form.submit('Post')}</p>
    ${c.form.end()}
</div>

<%def name="title()">Reply</%def>
