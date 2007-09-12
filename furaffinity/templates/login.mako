<%inherit file="base.mako" />

${h.form(h.url(controller='auth', action='login_check'), method='post')}
<div><label for="username">Username:</label><span>${h.text_field('username')}</span></div>
<div><label for="password">Password:</label><span>${h.password_field('password')}</span></div>
${h.submit('Login')}
${h.end_form()}

<%def name="title()">Login</%def>

