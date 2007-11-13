<%inherit file="../base.mako" />

<div id="news_page">
    <div class="recent_news">
        <div class="news_story">
            ${h.form(h.url(controller='news', action='do_post'), method='post')}
            <div class="news_form">
                <label for="title">Headline:</label>
                ${h.text_field('title', value=c.form_defaults['title'] or '')}
                % if 'title' in c.form_errors:
                    <span class="error">${c.form_errors['title']}</span>
                % endif
            </div>
            <div class="news_form">
                ${h.text_area('content', size="80x10", content=c.form_defaults['content'] or '')}
                <div>
                    % if 'content' in c.form_errors:
                        <span class="error">${c.form_errors['content']}</span>
                    % endif
                </div>
            </div>
            <div class="news_admin">
                <span class="checkbox_text">
                    <label for="is_anonymous">Anonymous?</label>
                    ${h.check_box('is_anonymous')}
                </span>
                ${h.submit('Post')}
                ${h.link_to('Cancel', h.url(controller='news', action='index', id=''))}
                ${h.end_form()}
            </div>
        </div>
    </div>
</div>

<%def name="title()">Post News</%def>

