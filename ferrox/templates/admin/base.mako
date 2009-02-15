<%inherit file="../base.mako" />

<ul id="submenu">
    <li>${h.HTML.a('Status?', href=h.url_for(controller='admin', action='index'))}</li>
    <li>${h.HTML.a('IP list', href=h.url_for(controller='admin', action='ip'))}</li>
    <li>${h.HTML.a('Config', href=h.url_for(controller='admin', action='config'))}</li>
</ul>

${next.body()}

<%def name="title()">${next.title()} - Admin control</%def>

