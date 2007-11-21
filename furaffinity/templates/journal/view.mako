<%inherit file="/base.mako" />

<big><big>${c.journal_entry_title}</big></big><br>
<big>by: ${c.journal_entry_author}</big><br>
% if c.is_mine:
${h.link_to('Edit', h.url(controller='journal', action='edit', username=None, id=c.journal_entry_id))}
${h.link_to('Delete', h.url(controller='journal', action='delete', username=None, id=c.journal_entry_id))}<br>
% endif
Content: ${c.journal_entry_content}<br>
Submitted at: ${c.journal_entry_time}<br><br>

${c.misc}
<%def name="title()">${c.journal_entry_title} by ${c.journal_entry_author}</%def>

