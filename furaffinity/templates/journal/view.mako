<%inherit file="/base.mako" />

<big><big>${c.journal_entry.title}</big></big><br>
<big>by: ${self.user_link(c.journal_entry.user)}</big><br>
% if c.is_mine:
${h.link_to('Edit', h.url(controller='journal', action='edit', username=c.route['username'], id=c.route['id']))}
${h.link_to('Delete', h.url(controller='journal', action='delete', username=c.route['username'], id=c.route['id']))}<br>
% endif
Content: ${c.journal_entry.content_parsed}<br>
Submitted at: ${h.format_time(c.journal_entry.time)}<br><br>

${c.misc}
<%def name="title()">${c.journal_entry_title} by ${c.journal_entry.user.display_name}</%def>

