<%inherit file="../base.mako" />

<div id="news_page">
    <span>News</span>
    <div class="recent_news">
        % for item in c.news:
        <div class="news_story">
            <div class="news_header">
                <div class="news_headline">${item.title}</div>
                <div class="news_author">By: ${item.author.display_name}</div>
                <div class="news_date">Date: ${item.time}</div>
            </div>
            <div class="news_content">${item.content}</div>
        </div>
        % endfor
    </div>
    <span>${h.link_to("Post", h.url(controller='news', action='post'))}</span>
</div>

<%def name="title()">News</%def>

