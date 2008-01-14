<%def name="news_entry(entry)">
<%
    if entry.is_deleted:
        if not c.auth_user.can('administrate'):
            return ''
        extra_class = ' deleted'
    else:
        extra_class = ''
%>
<div class="entry${extra_class}">
    <div class="header">
        <div class="title">${entry.title}</div>
        <div class="avatar FINISHME"><img src="http://userpic.livejournal.com/41114350/600603" alt="avatar"/></div>
        <%
            if entry.is_anonymous:
                author_string = 'FA Staff'
            else:
                author_string = capture(user_link, entry.author)
        %>
        <div class="author">By: ${author_string}</div>
        <div class="date">Date: ${h.format_time(entry.time)}</div>
    </div>
    <div class="content">
        ${entry.content}
    </div>
    % if c.auth_user.can('administrate'):
    ${h.form(h.url(controller='news', action='edit', id=entry.id), method='post')}
    <ul class="inline admin">
        <li>${h.link_to("Edit", h.url(controller='news', action='edit', id=entry.id))}</li>
        % if entry.is_deleted:
        <li>${h.submit('Undelete')}</li>
        % else:
        <li>${h.submit('Delete')}</li>
        % endif
    </ul>
    ${h.end_form()}
    % endif
</div>
</%def>

<%def name="journal_entry(entry)">
<%
    if entry.status == 'deleted':
        if not c.auth_user.can('administrate'):
            return ''
        extra_class = ' deleted'
    else:
        extra_class = ''
%>
<div class="entry${extra_class}">
    <div class="header">
        <div class="title">${entry.title}</div>
        <div class="avatar FINISHME"><img src="http://userpic.livejournal.com/41114350/600603" alt="avatar"/></div>
        <div class="author">By: ${user_link(entry.user)}</div>
        <div class="date">Date: ${h.format_time(entry.time)}</div>
    </div>
    <div class="content">
        ${entry.content}
    </div>
    % if c.auth_user.can('administrate'):
    ${h.form(h.url(controller='journal', action='edit', username=entry.user.username, id=entry.id), method='post')}
    <ul class="inline admin">
        <li>${h.link_to("Edit", h.url(controller='journal', action='edit', username=entry.user.username, id=entry.id))}</li>
        % if entry.status == 'deleted':
        <li>${h.submit('Undelete')}</li>
        % else:
        <li>${h.submit('Delete')}</li>
        % endif
    </ul>
    ${h.end_form()}
    % endif
</div>
</%def>

<%def name="user_link(user)">
    <span class="userlink">
        <a href="${h.url_for(controller='user', action='view', username=user.username)}"><img src="/images/foxy.gif" alt="[user]"/></a>
        <a href="${h.url_for(controller='user', action='view', username=user.username)}">${user.username}</a>
<!--
        <div class="popup">
            <img src="/images/foxy.gif" alt="" class="avatar"/>
            <div class="name">${user.role.sigil}${user.display_name}</div>
            <div class="role">${user.role.name}</div>
            <div class="rel">Not <a href="/users/eevee/watch">watched</a> by you</div>
            <div class="rel">Has you friended</div>
            <div class="links">
                <a href="${h.url_for(controller='user', action='view', username=user.username)}">Profile</a> |
                <a href="${h.url_for(controller='gallery', action='user_index', username=user.username)}">Gallery</a> |
                <a href="${h.url_for(controller='journal', action='index', username=user.username)}">Journal</a>
            </div>
            % if user.is_online():
            <div class="online">online</div>
            % else:
            <div class="offline">offline</div>
            % endif
        </div>
-->
    </span>
</%def>
