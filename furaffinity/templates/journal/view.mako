<%inherit file="/base.mako" />

<big><big>${c.journal_entry_title}</big></big><br>
<big>by: ${c.journal_entry_author}</big><br>
Content: ${c.journal_entry_content}<br>
Submitted at: ${c.journal_entry_time}<br><br>

${c.misc}
<%def name="title()">${c.journal_entry_title} by ${c.journal_entry_author}</%def>

