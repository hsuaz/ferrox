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
</div>

<%def name="title()">Index</%def>

