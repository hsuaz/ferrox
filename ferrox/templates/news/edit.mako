<%namespace name="lib" file="/lib.mako"/>
<%inherit file="../base.mako" />

<div class="basic-box">
    <h2>Edit News</h2>

    ${c.form.start(h.url(controller='news', action='edit_commit', id=c.item.id), method='post')}
    <dl class="standard-form">
        <dt>Headline</dt>
        <dd>${c.form.text_field('title')}</dd>
        <dt>Anonymous</dt>
        <dd>${c.form.check_box('is_anonymous')}</dd>
        <dt>Author</dt>
        <dd>${lib.user_link(c.item.author)}</dd>
        <dt>Date</dt>
        <dd>${h.format_time(c.item.time)}</dd>
        <dt>Select Avatar</dt>
        <dd>${lib.avatar_selector(c.item.author, c.item.avatar_id)}</dd>
    </dl>
    <p>${c.form.text_area('content', size="80x10")}</p>
    <p>${c.form.submit('Save')}</p>
    ${c.form.end()}
</div>

<%def name="title()">Edit News</%def>

