<%namespace name="lib" file="/lib.mako"/>
<%inherit file="../base.mako"/>

<ul class="submenu">
    <li>${h.HTML.a('Useless index', href=h.url_for(controller='user_settings', action='index', username=c.route['username']))}</li>
    <li>${h.HTML.a('Avatars', href=h.url_for(controller='user_settings', action='avatars', username=c.route['username']))}</li>
    <li>${h.HTML.a('Relationships', href=h.url_for(controller='user_settings', action='relationships', username=c.route['username']))}</li>
</ul>

${next.body()}
