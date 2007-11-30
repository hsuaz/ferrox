<%inherit file="../base.mako" />

<div id="news_page">
    <span>Journal for ${self.user_link(c.page_owner)}</span>
    <div class="recent_news">
    % if c.journals:
        % for item in c.journals:
        <div class="journal">
            <div class="journal_header">
                <div class="journal_title">${h.link_to(item.title, h.url(controller='journal', action='view', id=item.id, username=None))}</div>
                <div class="journal_date">Date: ${item.time}</div>
                % if c.is_mine:
                <div class="journal_controls">
                    ${h.link_to('Edit', h.url(controller='journal', action='edit', username=None, id=item.id))}
                    ${h.link_to('Delete', h.url(controller='journal', action='delete', username=None, id=item.id))}
                </div>
                % endif
            </div>
            <div class="journal_content">${item.content}</div>
        </div>
        % endfor
    % else:
        <div class="journal">
            <div class="journal_header">
                <div class="journal_title">Error</div>
            </div>
            <div class="journal_content">No journals found for user ${self.user_link(c.page_owner)}.</div>
        </div>
    % endif
    </div>
    % if c.is_mine:
    <span>${h.link_to('Post', h.url(controller='journal', action='post', username=None))}</span>
    % endif
</div>

<%def name="title()">Journal for ${c.page_owner.display_name}</%def>

