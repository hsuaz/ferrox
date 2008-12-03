<%namespace name="lib" file="/lib.mako"/>
<%namespace name="comments" file="/comments/lib.mako"/>
<%inherit file="/base.mako" />

<p>${h.link_to("&laquo; All of %s's entries" % c.journal_entry.user.display_name, h.url(controller='journal', action='index', username=c.journal_entry.user.username))}</p>
<div class="basic-box">
    <h2> ${h.image_tag('/images/icons/h2-journal.png', '')} ${c.journal_entry.user.display_name}'s Journal </h2>
    ${lib.journal_entry(c.journal_entry, False)}

    ${c.misc}
</div>

<div class="basic-box">
    <h2> ${h.image_tag('/images/icons/h2-comments.png', '')} Comments </h2>
    ${comments.comment_tree(c.journal_entry.discussion.comments, h.url_for(**c.route))}
</div>

<%def name="title()">${c.journal_entry.title} by ${c.journal_entry.user.display_name}</%def>
