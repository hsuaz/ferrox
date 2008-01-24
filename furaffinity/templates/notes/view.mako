<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<p>${h.link_to('&laquo; Inbox', h.url(controller='notes', action='user_index', username=c.page_owner.username))}</p>
<div class="basic-box">
    <h2>Note</h2>

    % for note in c.all_notes:
    ${lib.note_entry(note)}
    % endfor
</div>

<%def name="title()">${c.note.subject}</%def>

