<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<p> ${c.ip_nav} </p>

<table class="standard_table">
    <tr>
        <th> IP </th>
        <th> User </th>
        <th> From </th>
        <th> To </th>
    </tr>
    % for ip_log_entry in c.ip_page:
    <tr>
        <td> ${h.ip_to_string(ip_log_entry.ip)} </td>
        <td> ${lib.user_link(ip_log_entry.user)} </td>
        <td> ${h.format_time(ip_log_entry.start_time)} </td>
        <td> ${h.format_time(ip_log_entry.end_time)} </td>
    </tr>
    % endfor
</table>

<p> ${c.ip_nav} </p>

<%def name="title()">IP control</%def>

