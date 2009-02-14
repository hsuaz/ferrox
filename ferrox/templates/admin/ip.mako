<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<table class="standard_table">
    <tr>
        <th> IP </th>
        <th> User </th>
        <th> From </th>
        <th> To </th>
    </tr>
    % for ip_log_entry in c.ips:
    <tr>
        <td> ${ip_log_entry.ip} </td>
        <td> ${lib.user_link(ip_log_entry.user)} </td>
        <td> ${h.format_time(ip_log_entry.start_time)} </td>
        <td> ${h.format_time(ip_log_entry.end_time)} </td>
    </tr>
    % endfor
</table>

<p>
    % for link in c.paging_links:
        % if link[0] == 'submit':
            ${h.HTML.a(link[1], href=h.url_for(controller='admin', action='ip', page=link[1]))}
        % else:
            ${link[1]}
        % endif
    % endfor
</p>

<%def name="title()">IP control</%def>

