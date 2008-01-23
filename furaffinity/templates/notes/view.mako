<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<p>${h.link_to('&laquo; Inbox', h.url(controller='notes', action='user_index', username=c.page_owner.username))}</p>
<div class="basic-box">
    <h2>Note</h2>

    ${lib.note_entry(c.note)}
</div>

<%def name="title()">${c.note.subject}</%def>

