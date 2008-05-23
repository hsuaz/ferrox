<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${lib.user_linkbar(c.user)}


% if c.user == c.auth_user:
${c.empty_form.start(h.url(controller='user', action='relationships_change', username=c.user.username))}
<table>
<thead>
<tr>
<td>User</td>
<td>Watch Submissions</td>
<td>Watch Journals</td>
<td>Friend</td>
<td>Block</td>
</td>
</thead>
<tbody>
% for r in c.user.relationships:
    <tr>
    <td>${lib.user_link(r.target)} </td>
    <td>${c.empty_form.check_box("ws_%d"%r.target.id, checked=('watching_submissions' in r.relationship))}</td>
    <td>${c.empty_form.check_box("wj_%d"%r.target.id, checked=('watching_journals' in r.relationship))}</td>
    <td>${c.empty_form.check_box("f_%d"%r.target.id, checked=('friend_to' in r.relationship))}</td>
    <td>${c.empty_form.check_box("b_%d"%r.target.id, checked=('blocking' in r.relationship))}</td>
    </tr>
% endfor
</tbody>
</table>
${c.empty_form.submit('Apply Changes')}
${c.empty_form.end()}
% else:
<table>
<thead>
<tr>
<td>Watching</td>
</tr>
</thead>
<tbody>
% for r in c.user.relationships:
    % if 'wathing_submissions' in r.relationship or 'watching_journals' in r.relationship:
        <tr>
        <td>${lib.user_link(r.target)} </td>
        </tr>
    % endif
% endfor
</tbody>
</table>

<hr>

<table>
<thead>
<tr>
<td>Friends</td>
</tr>
</thead>
<tbody>
% for r in c.user.relationships:
    % if 'friend_to' in r.relationship:
        <tr>
        <td>${lib.user_link(r.target)} </td>
        <!-- (${h.link_to('&Delta;', h.url_for(controller='user', action='watch', username=r.target.username))}) -->
        </tr>
    % endif
% endfor
</tbody>
</table>
% endif

<%def name="title()">Relationships for ${c.user.display_name}</%def>
