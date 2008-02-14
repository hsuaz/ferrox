<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div class="basic-box">
    <h2>Send note</h2>

    ${c.form.start(h.url(controller='notes', action='write_send', username=c.route['username']), method='post')}
    % if c.route['action'] == 'reply':
    <p>
        ${'Replying to' if c.note.recipient == c.auth_user else 'Continuing'}
        ${h.link_to(c.note.base_subject(), h.url(controller='notes', action='view', username=c.route['username'], id=c.route['id']))}
        ${c.form.hidden_field('reply_to_note')}
    </p>
    % elif c.route['action'] == 'forward':
    <p>
        Forwarding
        ${h.link_to(c.note.base_subject(), h.url(controller='notes', action='view', username=c.route['username'], id=c.route['id']))}
    </p>
    % endif
    <dl class="standard-form">
        % if c.reply_to_note:
        <dt>To</dt>
        <dd>${lib.user_link(c.recipient)}</dd>
        % else:
        <dt>To</dt>
        <dd>${c.form.text_field('recipient')}</dd>
        % endif
        <dt>Subject</dt>
        <dd>${c.form.text_field('subject')}</dd>
        <dt>Message</dt>
        <dd>${c.form.text_area('content', size='80x10')}</dd>
    </dl>
    <p>${c.form.submit('Send')}</p>
    ${c.form.end()}
</div>

<%def name="title()">Send Note</%def>

