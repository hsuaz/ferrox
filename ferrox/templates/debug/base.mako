<%inherit file="../base.mako" />

<ul id="submenu">
    <li>${h.link_to('Index', h.url_for(controller='debug', action='index'))}</li>
    <li>${h.link_to('Crash', h.url_for(controller='debug', action='crash'))}</li>
</ul>

${next.body()}

<%def name="title()">${next.title()} - Debug</%def>

