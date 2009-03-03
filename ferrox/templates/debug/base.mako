<%inherit file="../base.mako" />

<ul id="submenu">
    <li>${h.HTML.a('Index', href=h.url_for(controller='debug', action='index'))}</li>
    <li>${h.HTML.a('Crash', href=h.url_for(controller='debug', action='crash'))}</li>
</ul>

${next.body()}

<%def name="title()">${next.title()} - Debug</%def>

