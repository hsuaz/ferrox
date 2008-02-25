<%inherit file="base.mako" />

${c.form.start(h.url(controller='index', action='register_check'), method='post')}
${c.form.hidden_field('remote_addr', value=c.environ['REMOTE_ADDR'])}
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

<script type="text/javascript"
   src="http://api.recaptcha.net/challenge?k=6LcAvAAAAAAAAOALs_m6x_L0_tsfRx3m_huHIS75">
</script>

<noscript>
   <iframe src="http://api.recaptcha.net/noscript?k=6LcAvAAAAAAAAOALs_m6x_L0_tsfRx3m_huHIS75"
       height="300" width="500" frameborder="0"></iframe><br>
   <textarea name="recaptcha_challenge_field" rows="3" cols="40">
   </textarea>
   <input type="hidden" name="recaptcha_response_field"
       value="manual_challenge">
</noscript>

% if 'recaptcha' in c.form.errors:
<p>${c.form.error('Captcha invalid.')}</p>
% endif

<p>${c.form.check_box('TOS_accept', label='I have read and agree to the Terms of Service')}</p>

<p>${c.form.submit('Register')}</p>
${c.form.end()}

<%def name="title()">Register</%def>
