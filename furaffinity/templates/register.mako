<%inherit file="base.mako" />

${h.form(h.url(controller='index', action='register_check'), method='post')}
<dl class="standard-form">
    <dt>Username</dt>
    <dd>${h.text_field('username')}</dd>
    <dt>Email</dt>
    <dd>
        ${h.text_field('email')} <br/>
        ${h.text_field('email_confirm')}
    </dd>
    <dt>Password</dt>
    <dd>
        ${h.password_field('password')} <br/>
        ${h.password_field('password_confirm')}
    </dd>
</dl>
<p>${h.submit('Register')}</p>
${h.end_form()}

<%def name="title()">Register</%def>

