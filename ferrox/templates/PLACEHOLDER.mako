<%inherit file="base.mako" />

<div id="PLACEHOLDER">
This page is a PLACEHOLDER.  It does not exist and/or work yet.  Should probably fix that before release, chief.
</div>

% if next:
    ${next.body()}
% endif

<%def name="title()">PLACEHOLDER</%def>

