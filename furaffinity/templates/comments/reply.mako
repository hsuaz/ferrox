<%namespace name="lib" file="/lib.mako"/>
<%namespace name="comments" file="/comments/lib.mako"/>
<%inherit file="base.mako" />

${comments.comment_tree([c.comment], c.discussion_url)}

<div class="basic-box">
    <h2>Reply</h2>

    ${c.form.start(h.url(controller='comments', action='reply_commit', id=c.route['id'], discussion_url=c.discussion_url), method='post')}
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
