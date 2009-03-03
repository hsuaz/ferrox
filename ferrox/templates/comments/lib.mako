<%namespace name="lib" file="/lib.mako"/>

<%def name="comment_tree(comments, post_url)">
% for comment in h.indented_comments(comments):
${single_comment(comment, post_url)}
% endfor
</%def>

<%def name="single_comment(comment, post_url)">
<div class="comment" style="margin-left: ${40 * comment.indent}px;">
    <div class="header">
        <div class="author">
            ${lib.user_link(comment.user)}
            <div class="avatar FINISHME"><img src="http://a.furaffinity.net/${comment.user.username}.gif" alt="avatar"/></div>
        </div>
        <div class="title">
<%
    if comment.title:
        comment_title = comment.title
    else:
        comment_title = h.literal('<span class="notitle">(no subject)</span>')
%>
            ${h.HTML.a(comment_title, href=h.url_for(controller='comments', action='view', post_url=post_url, id=comment.id))}</li>
        </div>
        <div class="date">${h.format_time(comment.time)}</div>
    </div>
    <div class="message">
        ${comment.content_parsed}
    </div>
    <ul class="inline actions">
        <li>${h.HTML.a(h.image_tag('/images/icons/link-reply.png', ''), ' Reply', href=h.url_for(controller='comments', action='reply', post_url=post_url, id=comment.id), class_='button')}</li>
        % if comment.get_parent():
        <li>${h.HTML.a(h.image_tag('/images/icons/link-parent.png', ''), ' Parent', href=h.url_for(controller='comments', action='view', post_url=post_url, id=comment.get_parent().id), class_='button')}</li>
        % endif
    </ul>
</div>
</%def>
