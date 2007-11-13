<%inherit file="../base.mako" />

<div id="news_page">
    <div class="recent_news">
        <div class="news_story">
            ${h.form(h.url(controller='news', action='do_edit'), method='post')}
            <div class="news_header">
                <div class="news_headline">
                    ${h.text_field('title', value=c.form_defaults['title'] or '')}
                    % if 'title' in c.form_errors:
                        <span class="error">${c.form_errors['title']}</span>
                    % endif
                </div>
                <div class="news_author">
                    By: ${c.item.author.display_name}
                    (Anonymous? ${h.check_box('is_anonymous', checked=c.item.is_anonymous)})
                </div>
                <div class="news_date">Date: ${c.item.time.strftime("%T %D")}</div>
            </div>
            <div class="news_form">
                ${h.text_area('content', size="80x10", content=c.form_defaults['content'] or '')}
                % if 'content' in c.form_errors:
                    <span class="error">${c.form_errors['content']}</span>
                % endif
            </div>
            ${h.submit('Save')}
            ${h.link_to('Cancel', h.url(controller='news', action='index', id=''), class_="small")}
            ${h.end_form()}
        </div>]]
    </div> 
</div>

<%def name="title()">Edit News</%def>

