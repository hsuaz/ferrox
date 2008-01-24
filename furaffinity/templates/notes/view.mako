<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<p>${h.link_to('&laquo; Inbox', h.url(controller='notes', action='user_index', username=c.page_owner.username))}</p>
% if c.note != c.latest_note:
<p>${h.link_to('Latest note in this conversation', h.url(controller='notes', action='view', username=c.page_owner.username, id=c.latest_note.id))}</p>
% endif
<div class="basic-box">
    <h2>Note</h2>

    % for note in c.all_notes:
    % if note.time >= c.latest_note.time or note == c.note:
    ${lib.note_entry(note, c.page_owner)}
    % else:
    ${lib.note_collapsed_entry(note, c.page_owner)}
    % endif
    % endfor
</div>

<%def name="title()">${c.note.subject}</%def>

