<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

<div class="basic-box TODO">
    <h2>${h.image_tag('/images/icons/h2-relationships.png', '')} Edit Relationships</h2>

    ${c.form.start(h.url_for(controller='user_settings', action='relationships_commit', username=c.user.username))}
    <table class="standard-table relationships">
    <thead>
    <tr>
        <th> </th>
        <th> Friend </th>
        <th> Watching <br/> Submissions </th>
        <th> Watching <br/> Journals </th>
        <th> Blocked </th>
    </tr>
    </thead>
    <tbody>
    % for user in c.relationship_order:
    % if user == c.other_user:
    <tr class="addition">
    % else:
    <tr>
    % endif
        <th> ${lib.user_link(user)} ${c.form.hidden_field('users', value=user.username)} </th>
        % for relationship in 'friend_to', 'watching_submissions', \
                              'watching_journals', 'blocking':
        <td>${c.form.check_box('user:%s' % user.username, value=relationship, checked=(relationship in c.relationships[user]))}</td>
        % endfor
    </tr>
    % endfor
    </tbody>
    </table>
    ${c.form.submit('Apply Changes')}
    ${c.form.end()}
</div>

<%def name="title()">Edit Relationships for ${c.user.display_name}</%def>
