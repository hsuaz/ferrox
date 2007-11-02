<%inherit file="base.mako" />

${h.form(h.url('login_check'), method='post')}
<dl class="standard-form">
    <dt><label for="username">Username</label></dt>
    <dd>${h.text_field('username', value=c.prefill.get('username'))}</dd>
    <dt><label for="password">Password</label></dt>
    <dd>${h.password_field('password')}</dd>
</dl>
${h.submit('Login')}
${h.end_form()}

<%def name="title()">Login</%def>

