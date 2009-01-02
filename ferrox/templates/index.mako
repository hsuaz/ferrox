<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div class="columns32-left">
    <div class="basic-box">
        <h2>${h.image_tag('/images/icons/h2-gallery.png', '')} Recent Submissions</h2>
        ${lib.thumbnail_grid(c.recent_submissions)}
    </div>
</div>
<div class="columns32-right">
    <div class="basic-box">
        <h2>${h.image_tag('/images/icons/h2-news.png', '')} News</h2>
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

