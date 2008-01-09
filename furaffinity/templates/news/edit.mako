<%inherit file="../base.mako" />

<div id="news_page">
    <div class="recent_news">
        <div class="news_story">
            ${h.form(h.url(controller='news', action='do_edit', id=c.id), method='post')}
            <div class="news_header">
                <div class="news_headline">
                    ${h.text_field('title', value=c.form_defaults['title'] or '')}
                    % if 'title' in c.form_errors:
                        <span class="error">${c.form_errors['title']}</span>
                    % endif
                </div>
                <div class="news_author">
                    By: ${self.user_link(c.item.author)}
                    (Anonymous? ${h.check_box('is_anonymous', checked=c.item.is_anonymous)})
                </div>
                <div class="news_date">Date: ${h.format_time(c.item.time)}</div>
            </div>
            <div class="news_form">
                ${h.text_area('content', size="80x10", content=c.form_defaults['content'] or '')}
                % if 'content' in c.form_errors:
                    <span class="error">${c.form_errors['content']}</span>
                % endif
            </div>
            ${h.submit('Save')}
            ${h.link_to('Cancel', h.url(controller='news', action='index'), class_="small")}
            ${h.end_form()}
        </div>
    </div> 
</div>

<%def name="title()">Edit News</%def>

