<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div class="basic-box">

    <h2>Deleting submission ${c.submission.title}
        % if c.auth_user != c.target_user:
            on behalf of ${lib.user_link(c.target_user)}
        % endif
    </h2>
    ${c.form.start(h.url_for(controller='gallery', action='delete_commit', id=c.submission.id, username=c.target_user.username), method='post')}

    <dl class="standard-form">
        <dt>Public Reason</dt>
        <dd>${c.form.text_field('public_reason')}</dd>
        <dt>Private Reason</dt>
        <dd>${c.form.text_field('private_reason')}</dd>
    </dl>
    <p>Are you sure you want to delete the submission ${c.submission.title} for user ${c.target_user.display_name}?

    ${c.empty_form.submit('Yes', name='confirm')}
    ${c.empty_form.submit('No', name='cancel')}
    </p>
    ${c.form.end()}
</div>

<%def name="title()">Delete Submission</%def>

