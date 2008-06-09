<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${lib.user_linkbar(c.user)}

${c.form.start(h.url(controller='user', action='relationships_change', username=c.user.username))}
<table class="relationships">
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
    <th>${lib.user_link(user)} </th>
    % for relationship in 'friend_to', 'watching_submissions', \
                          'watching_journals', 'blocking':
    <td>${c.form.check_box(user.username, value=relationship, checked=(relationship in c.relationships[user]))}</td>
    % endfor
</tr>
% endfor
</tbody>
</table>
${c.form.submit('Apply Changes')}
${c.form.end()}

<%def name="title()">Edit Relationships for ${c.user.display_name}</%def>
