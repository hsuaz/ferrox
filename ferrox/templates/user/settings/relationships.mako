<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${c.form.start(h.url(controller='user_settings', action='relationships_commit', username=c.user.username))}
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
<tr>
% else:
<tr class="addition">
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

<%def name="title()">Edit Relationships for ${c.user.display_name}</%def>
