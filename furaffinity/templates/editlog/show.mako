<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div id="news_page">
    <span>Edit log for ${c.information}</span>
    <div class="editlog">
    % if c.editlog_entries:
        % for item in c.editlog_entries:
        ---
        <div class="entry">
            <div class="entry_header">
                <div class="entry_title">Old Title: ${item['previous_title']}</div>
                <div class="entry_date">Edited on: ${h.format_time(item['edited_at'])}</div>
            </div>
            <div class="entry_info">
                Edited By: ${lib.user_link(item['edited_by'])}<br>
                Old text: ${item['previous_text_parsed']}<br>
            </div>
        </div>
        % endfor
    % else:
        <div class="entry">
            <div class="entry_header">
                <div class="entry_title">Error</div>
            </div>
            <div class="entry_info">
                No entries found for ${c.information}.
            </div>
        </div>
    % endif
    </div>
</div>

<%def name="title()">Edit log for ${c.information}</%def>
