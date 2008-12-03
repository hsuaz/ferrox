<%namespace name="lib" file="/lib.mako"/>
<%namespace name="comments" file="/comments/lib.mako"/>
<%inherit file="/base.mako" />

<div class="basic-box">
    <p>${h.link_to("&laquo; All of %s's entries" % c.journal_entry.user.display_name, h.url(controller='journal', action='index', username=c.journal_entry.user.username))}</p>
    ${lib.journal_entry(c.journal_entry, False)}

    ${c.misc}
</div>

${comments.comment_tree(c.journal_entry.discussion.comments, h.url_for(**c.route))}

<%def name="title()">${c.journal_entry.title} by ${c.journal_entry.user.display_name}</%def>
