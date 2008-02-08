<%inherit file="base.mako" />
${h.form(h.url(controller='index', action='register_check'), method='post')}
${h.hidden_field('remote_addr', value=c.environ['REMOTE_ADDR'])}
<dl class="standard-form">
    <dt>Username</dt>
    <dd>
        ${h.text_field('username', value=c.form_defaults['username'] or '')}
        % if 'username' in c.form_errors:
            <span class="error">${c.form_errors['username']}</span>
        % endif
    </dd>
    <dt>Email</dt>
    <dd>
        ${h.text_field('email', value=c.form_defaults['email'] or '')} 
        % if 'email' in c.form_errors:
            <span class="error">${c.form_errors['email']}</span>
        % endif
        <br/>
        ${h.text_field('email_confirm', value=c.form_defaults['email_confirm'] or '')}
        % if 'email_confirm' in c.form_errors:
            <span class="error">${c.form_errors['email_confirm']}</span>
        % endif
    </dd>
    <dt>Password</dt>
    <dd>
        ${h.password_field('password')} 
        % if 'password' in c.form_errors:
            <span class="error">${c.form_errors['password']}</span>
        % endif
        <br/>
        ${h.password_field('password_confirm')}
        % if 'password_confirm' in c.form_errors:
            <span class="error">${c.form_errors['password_confirm']}</span>
        % endif
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

% if 'recaptcha' in c.form_errors:
    <p><span class="error">${c.form_errors['recaptcha']}</span></p>
% endif

<p>${h.check_box('TOS_accept')} I have read and agree to the Terms of Service</p>
% if 'TOS_accept' in c.form_errors:
    <span class="error">You must accept the Terms of Service to register.</span>
% endif

<p>${h.submit('Register')}</p>
${h.end_form()}

<%def name="title()">Register</%def>

