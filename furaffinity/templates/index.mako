<%inherit file="base.mako" />

<div id="main_page">
    <div id="recent">
        <div id="recent_artwork">
            <span>Recent Artwork</span>
            <div class="recent_work">
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
            </div>
            <div class="recent_work">
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
            </div>
        </div>
        <div id="recent_stories">
            <span>Recent Stories</span>
            <div class="recent_work">
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
            </div>
        </div>
        <div id="recent_poetry">
            <span>Recent Poetry</span>
            <div class="recent_work">
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
            </div>
        </div>
        <div id="recent_music">
            <span>Recent Music</span>
            <div class="recent_work">
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
                <div class="work">
                    ${h.image_tag("thumb.jpg", "foo")}
                </div>
            </div>
        </div>
    </div>
    <div id="news">
        <span>News</span>
        <div class="recent_news">
            % for item in c.news:
            <div class="news_story">
                <div class="news_header">
                    <div class="news_headline">${item.title}</div>
                    <div class="news_author">By: ${self.user_link(item.author)}</div>
                    <div class="news_date">Date: ${h.format_time(item.time)}</div>
                </div>
                <div class="news_content">${item.content}</div>
            </div>
            % endfor
        </div>
    </div>
</div>

<%def name="title()">Index</%def>

