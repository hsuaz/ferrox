<%namespace name="lib" file="/lib.mako"/>

<%def name="comment_tree(comments, post_url)">
% for comment in h.indented_comments(comments):
${single_comment(comment, post_url)}
% endfor
</%def>

<%def name="single_comment(comment, post_url)">
<div class="comment entry" style="margin-left: ${40 * comment.indent}px;">
    <div class="header">
        <div class="title">${comment.title}</div>
        <div class="avatar FINISHME"><img src="http://userpic.livejournal.com/41114350/600603" alt="avatar"/></div>
        <div class="author">${lib.user_link(comment.user)}</div>
        <div class="date">${h.format_time(comment.time)}</div>
        <ul class="micro-linkbar">
            <li>${h.link_to("%s Reply" % h.image_tag('/images/icons/mail-reply-sender.png', ''), h.url(controller='comments', action='reply', post_url=post_url, id=comment.id))}</li>
            <li>${h.link_to("%s Link" % h.image_tag('/images/icons/text-html.png', ''), h.url(controller='comments', action='view', post_url=post_url, id=comment.id))}</li>
            % if comment.get_parent():
            <li>${h.link_to("%s Parent" % h.image_tag('/images/icons/go-up.png', ''), h.url(controller='comments', action='view', post_url=post_url, id=comment.get_parent().id))}</li>
            % endif
        </ul>
    </div>
    <div class="content">
        ${comment.content_parsed}
    </div>
</div>
</%def>
