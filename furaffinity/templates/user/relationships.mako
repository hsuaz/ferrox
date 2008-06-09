<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${lib.user_linkbar(c.user)}

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
<tr>
    <th> ${lib.user_link(user)} </th>
    % for relationship in 'friend_to', 'watching_submissions', \
                          'watching_journals', 'blocking':
    % if relationship in c.relationships[user]:
    <td> &bull; </td>
    % else:
    <td> </td>
    % endif
    % endfor
</tr>
% endfor
</tbody>
</table>

<%def name="title()">Relationships for ${c.user.display_name}</%def>
