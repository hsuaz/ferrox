<%inherit file="base.mako" />

<p> This is a set of admin-only debugging pages, for..  debugging purposes. </p>

<dl>
    <dt>${h.link_to('Crash', h.url(controller='debug', action='crash'))}</dt>
    <dd>Throw a fatal error.</dd>

<%def name="title()">Index</%def>

