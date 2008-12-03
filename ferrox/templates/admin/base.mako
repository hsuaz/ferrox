<%inherit file="../base.mako" />

<ul id="submenu">
    <li>${h.link_to('Status?', h.url(controller='admin', action='index'))}</li>
    <li>${h.link_to('IP list', h.url(controller='admin', action='ip'))}</li>
</ul>

${next.body()}

<%def name="title()">${next.title()} - Admin control</%def>

