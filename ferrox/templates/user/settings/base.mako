<%namespace name="lib" file="/lib.mako"/>
<%inherit file="../base.mako"/>

<ul class="submenu">
    <li>${h.link_to('Useless index', h.url_for(controller='user_settings', action='index', username=c.route['username']))}</li>
    <li>${h.link_to('Avatars', h.url_for(controller='user_settings', action='avatars', username=c.route['username']))}</li>
    <li>${h.link_to('Relationships', h.url_for(controller='user_settings', action='relationships', username=c.route['username']))}</li>
</ul>

${next.body()}
