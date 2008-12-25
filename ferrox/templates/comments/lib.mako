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
            % if comment.title:
            ${comment.title}
            % else:
            <span class="notitle">(no subject)</span>
            % endif
        </div>
        <div class="date">${h.format_time(comment.time)}</div>
    </div>
    <div class="message">
        ${comment.content_parsed}
    </div>
    <ul class="inline actions">
        <li>${h.link_to("%s Reply" % h.image_tag('/images/icons/link-reply.png', ''), h.url(controller='comments', action='reply', post_url=post_url, id=comment.id), class_='button')}</li>
        <li>${h.link_to("%s Link" % h.image_tag('/images/icons/link-link.png', ''), h.url(controller='comments', action='view', post_url=post_url, id=comment.id), class_='button')}</li>
        % if comment.get_parent():
        <li>${h.link_to("%s Parent" % h.image_tag('/images/icons/link-parent.png', ''), h.url(controller='comments', action='view', post_url=post_url, id=comment.get_parent().id), class_='button')}</li>
        % endif
    </ul>
</div>
</%def>
