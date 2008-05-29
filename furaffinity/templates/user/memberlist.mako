<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

<table>
<thead>
<tr>
<td>Watching</td>
</tr>
</thead>
<tbody>
% for u in c.users:
        <tr>
        <td>${lib.user_link(u)} </td>
        </tr>
% endfor
</tbody>
</table>

<%def name="title()">Member List</%def>
