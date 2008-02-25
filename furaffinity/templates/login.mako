<%inherit file="base.mako" />

${c.form.start(h.url(controller='index', action='login_check'), method='post')}
<dl class="standard-form">
    <dt><label for="username">Username</label></dt>
    <dd>${c.form.text_field('username')}</dd>
    <dt><label for="password">Password</label></dt>
    <dd>${c.form.password_field('password')}</dd>
</dl>
${c.form.submit('Login')}
${c.form.end()}

<%def name="title()">Login</%def>
