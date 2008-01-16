<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div class="basic-box">
    <h2>Edit log for ${c.original.title}</h2>

    % if c.editlog_entries:
    % for item in c.editlog_entries:
    <div class="entry">
        <div class="edit-header">
            <div class="title">${item['previous_title']}</div>
            <div class="author">Edited by ${lib.user_link(item['edited_by'])} at ${h.format_time(item['edited_at'])}</div>
        </div>
        <div class="content">
            ${item['previous_text_parsed']}<br>
        </div>
    </div>
    % endfor
    % else:
    <p>No edits have been made.</p>
    % endif
</div>

<%def name="title()">Edit log for ${c.original.title}</%def>
