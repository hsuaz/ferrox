<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div id="left-column">
    <div class="basic-box">
        <h2>Recent Submissions</h2>
        ${lib.thumbnail_grid(c.recent_submissions)}
    </div>
</div>
<div id="right-column">
    <div class="basic-box">
        <h2>News</h2>
        % if c.auth_user.can('admin.auth'):
        <ul class="mini-linkbar">
<li class="admin">${h.link_to("%s Post news" % h.image_tag('/images/icons/document-new.png', ''), h.url_for(controller='news', action='post'))}</li>
        </ul>
        % endif
        % for item in c.news:
        ${lib.news_entry(item, True)}
        % endfor
    </div>
</div>

<%def name="title()">Index</%def>

