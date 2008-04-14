<%namespace name="lib" file="/lib.mako"/>
<%namespace name="comments" file="/comments/lib.mako"/>
<%inherit file="../base.mako" />

<div class="basic-box">
    <h2>News Archive</h2>
    % if c.auth_user.can("administrate"):
    <ul class="inline admin">
        <li>${h.link_to('Post News', h.url(controller = 'news', action='post'))}</li>
    </ul>
    % endif
    ${lib.news_entry(c.news, False)}
</div>
<p class="nav">
    ${c.newsnav}
</p>

${comments.comment_tree(c.news.comments, h.url_for(**c.route))}

<%def name="title()">${c.news.title} - News</%def>
