<%inherit file="base.mako"/>

<p> This is the userpage for ${c.user.display_name}! </p>

<%def name="title()">${c.user.display_name}</%def>
