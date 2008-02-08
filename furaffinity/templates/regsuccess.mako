<%inherit file="base.mako" />

<p>Your account has been successfully created, but it must be verified before you can log in.</p>
<p>Since we're not sending email yet, the verification link is below.</p>
<p>${c.verify_link}</p>
<%def name="title()">Register</%def>

