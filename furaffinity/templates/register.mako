<%inherit file="base.mako" />

${h.form(h.url(action='register_check'), method='post')}
<div><label for="username">Username:</label><span>${h.text_field('username')}</span></div>
<div><label for="email">Email:</label><span>${h.text_field('email')}</span></div>
<div><label for="email_confirm">Confirm Email:</label><span>${h.text_field('email_confirm')}</span></div>
<div><label for="password">Password:</label><span>${h.password_field('password')}</span></div>
<div><label for="password_confirm">Confirm Password:</label><span>${h.password_field('password_confirm')}</span></div>
${h.submit('Register')}
${h.end_form()}

<%def name="title()">Register</%def>

