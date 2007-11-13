<%inherit file="../base.mako" />

<div id="news_page">
    % if c.auth_user.can("administrate"):
        <div class="news_admin">
            ${h.link_to('Post News', h.url(controller = 'news', action='post'))}
        </div>
    % endif
    % for item in c.newspage:
        % if not item.is_deleted or c.auth_user.can("administrate"):
            % if item.is_deleted:
                <div class="news_story_deleted">
            % else:
                <div class="news_story">
            % endif
            <div class="news_header">
                <div class="news_headline">${item.title}</div>
                <div class="news_author">
                    By: 
                    % if item.is_anonymous:
                        FA Staff
                    % else:
                        ${item.author.display_name}
                    % endif
                </div>
                <div class="news_date">Date: ${item.time.strftime("%T %D")}</div>
            </div>
            <div class="news_content">${item.content}</div>
        </div>
        % endif
        % if c.auth_user.can("administrate"):
        <div class="news_admin_bottom">
            <span class="js-news-edit">
                ${h.link_to("Edit", h.url(controller="news", action="edit", id=item.id))}
            </span>
                % if item.is_deleted:
                    <span class="js-news-undelete">
                        ${h.link_to("Undelete", h.url(controller="news", action="undelete", id=item.id))}
                    </span>
                % else:
                    <span class="js-news-delete">
                        ${h.link_to("Delete", h.url(controller="news", action="delete", id=item.id))} 
                    </span>
                % endif
            </span>
        </div>
        % endif
    % endfor
    <div id="news_nav">
        ${c.newsnav}
    </div> 
    <span>${h.link_to("Post", h.url(controller='news', action='post'))}</span>
</div>

<%def name="title()">News</%def>

