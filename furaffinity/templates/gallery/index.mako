<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div id="news_page">
    <span>Gallery for ${c.page_owner.display_name}</span>
    <div class="recent_news">
    % if c.submissions:
        % for item in c.submissions:
        <div class="submission">
            <div class="submission_header">
                <div class="submission_title">${h.link_to(item['title'], h.url(controller='gallery', action='view', id=item['id'], username=c.page_owner.username))}</div>
                <div class="submission_date">Date: ${h.format_time(item['date'])}</div>
            </div>
            <div class="submission_info">
                ${item['description']}<br>
                % if item['thumbnail'] != None:
                <div class="submission_thumbnail">${h.image_tag(h.url_for(controller='gallery', action='file', filename=item['thumbnail']), item['title'])}</div>
                % endif
            </div>
        </div>
        % endfor
    % else:
        <div class="submission">
            <div class="submission_header">
                <div class="submission_title">Error</div>
            </div>
            <div class="submission_info">
                No submissions found for ${lib.user_link(c.page_owner)}.
            </div>
        </div>
    % endif
    </div>
    % if c.is_mine:
    <span>${h.link_to('Submit Art', h.url(controller='gallery', action='submit', username=c.page_owner.username))}</span>
    % endif
</div>

<%def name="title()">Gallery for ${c.page_owner.display_name}</%def>

