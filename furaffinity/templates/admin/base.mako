<%inherit file="../base.mako" />

<ul id="admin_menu">
    <li>${h.link_to('Status?', h.url(controller='admin'))}</li>
    <li>${h.link_to('IP list', h.url(controller='admin', action='ip'))}</li>
</ul>

${next.body()}

<%def name="title()">${next.title()} - Admin control</%def>

