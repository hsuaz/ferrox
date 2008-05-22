<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${lib.user_linkbar(c.user)}

% for r in c.user.relationships:
<p>${r.relationship} ${r.target.display_name}</p>
% endfor

<%def name="title()">Relationships for ${c.user.display_name}</%def>
