<%inherit file="base.mako" />

% if c.verified:
    <p>You have successfully verified your account.  You may now log into FurAffinity.</p>
% else:
    <p>Verification code incorrect.  Please check your email for the correct code and try again.</p>
% endif
<%def name="title()">Register</%def>

