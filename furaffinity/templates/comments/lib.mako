<%namespace name="lib" file="/lib.mako"/>

<%def name="comment_tree(comments, discussion_url)">
% for comment in h.indented_comments(comments):
${single_comment(comment, discussion_url)}
% endfor
</%def>

<%def name="single_comment(comment, discussion_url)">
<div class="comment entry" style="margin-left: ${40 * comment.indent}px;">
    <div class="header">
        <div class="title">${comment.subject}</div>
        <div class="avatar FINISHME"><img src="http://userpic.livejournal.com/41114350/600603" alt="avatar"/></div>
        <div class="author">${lib.user_link(comment.user)}</div>
        <div class="date">${h.format_time(comment.time)}</div>
        <ul class="micro-linkbar">
            <li>${h.link_to("%s Reply" % h.image_tag('/images/icons/mail-reply-sender.png', ''), h.url(controller='comments', action='reply', discussion_url=discussion_url, id=comment.id))}</li>
            <li>${h.link_to("%s Link" % h.image_tag('/images/icons/text-html.png', ''), h.url(controller='comments', action='view', discussion_url=discussion_url, id=comment.id))}</li>
            % if comment.get_parent():
            <li>${h.link_to("%s Parent" % h.image_tag('/images/icons/go-up.png', ''), h.url(controller='comments', action='view', discussion_url=discussion_url, id=comment.get_parent().id))}</li>
            % endif
        </ul>
    </div>
    <div class="content">
        ${comment.content_parsed}
    </div>
</div>
</%def>
