<%namespace name="lib" file="/lib.mako"/>
<%inherit file="../base.mako" />

<div class="basic-box">
    <h2>Edit News</h2>

    ${h.form(h.url(controller='news', action='edit_commit', id=c.form_defaults['id']), method='post')}
    <dl class="standard-form">
        <dt>Headline</dt>
        <dd>${h.text_field('title', value=c.form_defaults['title'] or '')}</dd>
        <div class="news_headline">
            % if 'title' in c.form_errors:
                <span class="error">${c.form_errors['title']}</span>
            % endif
        </div>
        <dt>Anonymous</dt>
        <dd>${h.check_box('is_anonymous', checked=c.item.is_anonymous)}</dd>
        <dt>Author</dt>
        <dd>${lib.user_link(c.item.author)}</dd>
        <dt>Date</dt>
        <dd>${h.format_time(c.item.time)}</dd>
    </dl>
    ${h.text_area('content', size="80x10", content=c.form_defaults['content'] or '')}
        % if 'content' in c.form_errors:
        <span class="error">${c.form_errors['content']}</span>
        % endif
    <p>${h.submit('Save')}</p>
    ${h.end_form()}
</div>

<%def name="title()">Edit News</%def>

