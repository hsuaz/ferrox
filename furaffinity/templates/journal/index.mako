<%inherit file="../base.mako" />

<div id="news_page">
    <span>Journal for ${c.page_owner.display_name}</span>
    <div class="recent_news">
    % if c.page_owner.journals:
        % for item in c.page_owner.journals:
        <div class="journal">
            <div class="journal_header">
                <div class="journal_title">${h.link_to(item.title, h.url(controller='journal', action='view', id=item.id, username=None))}</div>
                <div class="journal_date">Date: ${item.time}</div>
            </div>
            <div class="journal_content">${item.content}</div>
        </div>
        % endfor
    % else:
        <div class="journal">
            <div class="journal_header">
                <div class="journal_title">Error</div>
            </div>
            <div class="journal_content">No journals found for user ${c.page_owner.display_name}.</div>
        </div>
    % endif
    </div>
    % if c.is_mine:
    <span>${h.link_to('Post', h.url(controller='journal', action='post', username=None))}</span>
    % endif
</div>

<%def name="title()">Journal for ${c.page_owner.display_name}</%def>

