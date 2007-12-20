<%inherit file="../base.mako" />

<div id="news_page">
    <span>Journal for ${self.user_link(c.page_owner)}</span>
    <div class="recent_news">
    % if c.journal_page:
        % for item in c.journal_page:
        <div class="journal">
            <div class="journal_header">
                <div class="journal_title">${h.link_to(item.title, h.url(controller='journal', action='view', id=item.id, username=c.page_owner.username))}</div>
                <div class="journal_date">Date: ${h.format_time(item.time)}</div>
                % if c.is_mine:
                <div class="journal_controls">
                    ${h.link_to('Edit', h.url(controller='journal', action='edit', username=c.page_owner.username, id=item.id))}
                    ${h.link_to('Delete', h.url(controller='journal', action='delete', username=c.page_owner.username, id=item.id))}
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
    <p> ${c.journal_nav} </p>
    % if c.is_mine:
    <span>${h.link_to('Post', h.url(controller='journal', action='post', username=c.page_owner.username))}</span>
    % endif
</div>

<%def name="title()">Journal for ${c.page_owner.display_name}</%def>

