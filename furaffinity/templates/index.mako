<%inherit file="base.mako" />

<div id="left-column">
    <div class="basic-box">
        <h2>Recent Artwork</h2>
        <div class="thumbnail-grid">
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
        </div>
    </div>
    <div class="basic-box">
        <h2>Recent Stories</h2>
        <div class="thumbnail-grid">
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
        </div>
    </div>
    <div class="basic-box">
        <h2>Recent Poetry</h2>
        <div class="thumbnail-grid">
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
        </div>
    </div>
    <div class="basic-box">
        <h2>Recent Music</h2>
        <div class="thumbnail-grid">
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
            <div class="thumbnail">
                ${h.image_tag("thumb.jpg", "foo")}
            </div>
        </div>
    </div>
</div>
<div id="right-column">
    <div class="basic-box">
        <h2>News</h2>
        % for item in c.news:
        <div class="entry">
            <div class="header">
                <div class="title">${item.title}</div>
                <div class="avatar FINISHME"><img src="http://userpic.livejournal.com/41114350/600603" alt="avatar"/></div>
                <div class="author">By: ${self.user_link(item.author)}</div>
                <div class="date">Date: ${h.format_time(item.time)}</div>
            </div>
            <div class="content">
                ${item.content}
            </div>
        </div>
        <div class="entry">
            <div class="header">
                <div class="title">${item.title}</div>
                <div class="avatar FINISHME"><img src="/images/ad1.gif" alt="avatar"/></div>
                <div class="author">By: ${self.user_link(item.author)}</div>
                <div class="date">Date: ${h.format_time(item.time)}</div>
            </div>
            <div class="content">
                ${item.content}
            </div>
        </div>
        % endfor
    </div>
</div>

<%def name="title()">Index</%def>

