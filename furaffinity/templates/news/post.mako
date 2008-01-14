<%inherit file="../base.mako" />

<div class="basic-box">
    <h2>Post News</h2>

    ${h.form(h.url(controller='news', action='do_post'), method='post')}
    <dl class="standard-form">
        <dt>Headline</dt>
        <dd>${h.text_field('title', value=c.form_defaults['title'] or '')}
            % if 'title' in c.form_errors:
            <span class="error">${c.form_errors['title']}</span>
            % endif
        </dd>
        <dt>Anonymous</dt>
        <dd>${h.check_box('is_anonymous')}</dd>
    </dl>
    <p>${h.text_area('content', size="80x10", content=c.form_defaults['content'] or '')}</p>
        % if 'content' in c.form_errors:
        <p class="error">${c.form_errors['content']}</p>
        % endif
    <p>${h.submit('Post')}</p>
    ${h.end_form()}
</div>

<%def name="title()">Post News</%def>

