<%inherit file="../base.mako" />

<div id="news_page">
    <span>Journal for ${c.page_owner.display_name}</span>
    <div class="recent_news">
        % for item in c.page_owner.journals:
        <div class="news_story">
            <div class="news_header">
                <div class="journal_title">${item.title}</div>
                <div class="journal_date">Date: ${item.time}</div>
            </div>
            <div class="journal_content">${item.content}</div>
        </div>
        % endfor
    </div>
    <span>${h.link_to("Post", h.url(controller='journal', action='view', id=item.id, username=None))}</span>
</div>

<%def name="title()">Journal for ${c.page_owner.display_name}</%def>

