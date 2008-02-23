<%inherit file="../base.mako" />

<div class="basic-box">
    <h2>Post News</h2>

    ${c.form.start(h.url(controller='news', action='do_post'), method='post')}
    <dl class="standard-form">
        <dt>Headline</dt>
        <dd>${c.form.text_field('title')}</dd>
        <dt>Anonymous</dt>
        <dd>${c.form.check_box('is_anonymous')}</dd>
    </dl>
    <p>${c.form.text_area('content', size="80x10")}</p>
    <p>${c.form.submit('Post')}</p>
    ${c.form.end()}
</div>

<%def name="title()">Post News</%def>

