<%namespace name="lib" file="/lib.mako"/>
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
        ${lib.news_entry(item)}
        % endfor
    </div>
</div>

<%def name="title()">Index</%def>

