<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${lib.user_linkbar(c.user)}

<p> This is the userpage for ${c.user.display_name}! </p>

<%def name="title()">${c.user.display_name}</%def>
