<%inherit file="base.mako" />

${c.form.start(h.url_for(controller='index', action='register_check'), method='post')}
<dl class="standard-form">
    <dt>Username</dt>
    <dd>${c.form.text_field('username')}</dd>
    <dt>Email</dt>
    <dd>
        ${c.form.text_field('email')} <br/>
        ${c.form.text_field('email_confirm')}
    </dd>
    <dt>Password</dt>
    <dd>
        ${c.form.password_field('password')} <br/>
        ${c.form.password_field('password_confirm')}
    </dd>
</dl>

<p>${c.form.check_box('TOS_accept', label='I have read and agree to the Terms of Service')}</p>

<p>${c.form.submit('Register')}</p>
${c.form.end()}

<%def name="title()">Register</%def>
