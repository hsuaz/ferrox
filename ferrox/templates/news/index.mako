<%namespace name="lib" file="/lib.mako"/>
<%inherit file="../base.mako" />

<div class="basic-box">
    <h2>News Archive</h2>
    % if c.auth_user.can("news.manage"):
    <ul class="inline admin">
        <li>${h.link_to('Post news', h.url_for(controller='news', action='post'))}</li>
    </ul>
    % endif
    % for item in c.newsitems:
    ${lib.news_entry(item, True)}
    % endfor
</div>
<p class="nav">
    ${c.newsnav}
</p>

<%def name="title()">News</%def>

