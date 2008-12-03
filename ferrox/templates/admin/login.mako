<%inherit file="base.mako" />

${c.form.start(h.url(controller='admin', action='auth_verify'), method='post')}
% if c.auth_user and not c.auth_user.can('administrate'):
Please note that user ${c.auth_user.display_name} (${c.auth_user.username}) will be logged out.
% endif
<dl class="standard-form">
    <dt><label for="username">Username</label></dt>
    <dd>${c.form.text_field('username')}</dd>
    <dt><label for="password">Password</label></dt>
    <dd>${c.form.password_field('password')}</dd>
</dl>
${c.form.submit('Login as Administrator')}
${c.form.end()}

<%def name="title()">Login</%def>
