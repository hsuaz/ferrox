<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

${c.form.start(h.url_for(controller='admin', action='ban_commit'), method='post')}
<dl class="standard-form">
    <dt><label for="username">Username</label></dt>
    <dd>${c.form.text_field('username')}</dd>
    <dt><label for="expiration">Expiration</label></dt>
    <dd>${c.form.text_field('expiration')}</dd>
    <dt><label for="role_id">Set Role To</label></dt>
    <dd>${c.form.select('role_id', h.objects_to_option_tags(c.roles))}</dd>
    <dt><label for="reason">Reason</label></dt>
    <dd>${c.form.text_field('reason')}</dd>
    <dt><label for="notes">Admin Notes</label></dt>
    <dd>${c.form.text_field('notes')}</dd>
</dl>
${c.form.submit('Ban User')}
${c.form.end()}

<%def name="title()">Ban User</%def>

