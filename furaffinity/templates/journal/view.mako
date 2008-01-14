<%namespace name="lib" file="/lib.mako"/>
<%inherit file="/base.mako" />

<div class="basic-box">
    <p>${h.link_to("&laquo; All of %s's entries" % c.journal_entry.user.display_name, h.url(controller='journal', action='index', username=c.journal_entry.user.username))}</p>
    ${lib.journal_entry(c.journal_entry)}

    ${c.misc}
</div>

<%def name="title()">${c.journal_entry.title} by ${c.journal_entry.user.display_name}</%def>

