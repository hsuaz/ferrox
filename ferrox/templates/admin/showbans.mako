<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<table>
<thead>
<tr>
<td>Control</td>
<td>User</td>
<td>Banned By</td>
<td>Current Group</td>
<td>Expiration</td>
<td>Will revert to...</td>
<td>Reason</td>
<td>Admin Notes</td>
</tr>
</thead>
<tbody>
% for ban in c.bans:
<tr>
<td>...</td>
<td>${lib.user_link(ban.user)}</td>
<td>${lib.user_link(ban.admin)}</td>
<td>${ban.user.role.name}</td>
<td>${ban.expires if ban.expires else 'Never'}</td>
<td>${ban.revert_to.name}</td>
<td>${ban.reason}</td>
<td>${ban.admin_message}</td>
</tr>
% endfor
</tbody>
</table>

<%def name="title()">Login</%def>
