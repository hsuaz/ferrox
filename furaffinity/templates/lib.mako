<%def name="news_entry(entry, short)">
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
        <div class="title">${entry.subject}</div>
        <div class="avatar">
            % if not entry.is_anonymous:
            ${h.image_tag(h.get_avatar_url(entry), entry.user.username)}
            % else:
            <img src="${h.get_avatar_url()}" alt="default avatar"/>
            % endif
        </div>
        <%
            if entry.is_anonymous:
                author_string = 'FA Staff'
            else:
                author_string = capture(user_link, entry.user)
        %>
        <div class="author">By: ${author_string}</div>
        <div class="date">Date: ${h.format_time(entry.time)}</div>
    </div>
    <div class="content">
        % if short:
            ${entry.content_short}
        % else:
            ${entry.content_parsed}
        % endif
    </div>
    % if c.auth_user.can('administrate'):
    ${c.empty_form.start(h.url(controller='news', action='edit', id=entry.id), method='post')}
    <ul class="inline admin">
        <li>${h.link_to('Edit', h.url(controller='news', action='edit', id=entry.id))}</li>
        % if entry.is_deleted:
        <li>${c.empty_form.submit('Undelete')}</li>
        % else:
        <li>${c.empty_form.submit('Delete')}</li>
        % endif
    </ul>
    ${c.empty_form.end()}
    % endif

<% news_url = h.url_for(controller='news', action='view', id=entry.id) %>
    <ul class="inline">
        <li>${h.link_to('View comments', h.url(controller='comments', action='view', discussion_url=news_url))}</li>
        <li>${h.link_to('Reply', h.url(controller='comments', action='reply', discussion_url=news_url))}</li>
    </ul>
</div>
</%def>

<%def name="journal_entry(entry, short)">
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
        <div class="title">${h.link_to(entry.title, h.url(controller='journal', action='view', username=entry.user.username, year=entry.time.year, month=entry.time.month, day=entry.time.day, id=entry.id))}</div>
        <div class="avatar">${h.image_tag(h.get_avatar_url(entry), entry.user.display_name)}</div>
        <div class="author">By: ${user_link(entry.user)}</div>
        <div class="date">Date: ${h.format_time(entry.time)}</div>
    </div>
    <div class="content">
        % if short:
            ${entry.content_short}
        % else:
            ${entry.content_parsed}
        % endif
    </div>
    % if c.auth_user.can('administrate'):
    ${c.empty_form.start(h.url(controller='journal', action='edit', username=entry.user.username, id=entry.id), method='post')}
    <ul class="inline admin">
        <li>${h.link_to("Edit", h.url(controller='journal', action='edit', username=entry.user.username, id=entry.id))}</li>
        % if entry.status == 'deleted':
        <li>${c.empty_form.submit('Undelete')}</li>
        % else:
        <li>${c.empty_form.submit('Delete')}</li>
        % endif
    </ul>
    ${c.empty_form.end()}
    % endif
</div>
</%def>

<%def name="note_entry(note, owner)">
<div class="entry">
<%
    icon = ''
    if note.status == 'unread':
        icon = h.image_tag('/images/icons/mail-unread.png', 'Unread')
%>
    <div class="header">
        <div class="title">${note.subject}${icon}</div>
        <div class="avatar">${h.image_tag(h.get_avatar_url(owner), owner.display_name)}/div>
        % if note.sender == owner:
        <div class="author">${h.image_tag('/images/icons/go-next.png', 'Sent to')} ${user_link(note.recipient)}</div>
        % else:
        <div class="author">${h.image_tag('/images/icons/go-previous.png', 'Received from')} ${user_link(note.sender)}</div>
        % endif
        <div class="date">Date: ${h.format_time(note.time)}</div>
    </div>
    <ul class="micro-linkbar">
        <li>${h.link_to("%s Reply" % h.image_tag('/images/icons/mail-reply-sender.png', ''), h.url(controller='notes', action='reply', username=c.route['username'], id=note.id))}</li>
        <li>${h.link_to("%s Forward" % h.image_tag('/images/icons/mail-forward.png', ''), h.url(controller='notes', action='forward', username=c.route['username'], id=note.id))}</li>
    </ul>
    <div class="content">
        ${note.content_parsed}
    </div>
</div>
</%def>

<%def name="note_collapsed_entry(note, owner)">
<div class="entry collapsed">
    <div class="header">
        <div class="title">${h.link_to(note.subject, h.url(controller='notes', action='view', username=owner.username, id=note.id), class_='js-expand-note')}</div>
    </div>
</div>
</%def>

<%def name="user_link(user, care_about_online=True)">
<span class="userlink">
    <a href="${h.url_for(controller='user', action='view', username=user.username)}"><img src="/images/foxy.gif" alt="[user]"/></a>
    <a href="${h.url_for(controller='user', action='view', username=user.username)}" class="js-userlink-target">${user.username}</a>
</span>
</%def>

<%def name="user_linkbar(user)">
<ul class="mini-linkbar">
    <li class="not-link">${user.display_name}:</li>
    <li>${h.link_to('Overview', h.url_for(controller='user', action='view', username=user.username))}</li>
    <li>${h.link_to('Profile', h.url_for(controller='user', action='profile', username=user.username))}</li>
    <li>${h.link_to('Gallery', h.url_for(controller='gallery', action='index', username=user.username))}</li>
    <li>${h.link_to('Journal', h.url_for(controller='journal', action='index', username=user.username))}</li>
    % if c.auth_user:
    <li class="not-link"></li>
    <li>${h.link_to(h.image_tag('/images/icons/list-add.png', 'Watch'), h.url_for(controller='user', action='watch', username=user.username)) }</li>
    <li>${h.link_to(h.image_tag('/images/icons/mail-message-new.png', 'Send note'), h.url_for(controller='notes', action='write', username=c.auth_user.username, recipient=user.username))}</li>
    <li>${h.link_to(h.image_tag('/images/icons/process-stop.png', 'Block'), h.url_for(controller='user', action='block', username=user.username)) }</li>
    <li>${h.link_to(h.image_tag('/images/icons/list-add.png', 'Befriend'), h.url_for(controller='user', action='friend', username=user.username)) }</li>
    % endif
</ul>

</%def>

<%def name="avatar_selector(user, default=0, name='avatar_id')">
<select name="${name}">
<option value="0"${' selected="selected"' if default==0 else ''}>Default Avatar</option>
% for av in user.avatars:
<option value="${av.id}"${' selected="selected"' if default==av.id else ''}>${av.title}</option>
% endfor
</select>
</%def>

<%def name="thumbnail_grid(submissions)">
% if submissions:
<ul class="thumbnail-grid">
    % for submission in submissions:
    <li id="sub${submission.id}">
        <div class="popup">
            Description: ${submission.description_parsed}<br>
            Date: ${h.format_time(submission.time)}
        </div>
        % if submission.thumbnail:
        <div class="thumbnail">${h.link_to(h.image_tag(h.url_for(controller='gallery', action='file', filename=submission.thumbnail.mogile_key), submission.title), h.url(controller='gallery', action='view', id=submission.id, username=submission.primary_artist.username ))}</div>
        % endif
        <div class="title">${h.link_to(submission.title, h.url(controller='gallery', action='view', id=submission.id, username=submission.primary_artist.username))}</div>
        by ${h.link_to(submission.primary_artist.display_name, h.url(controller='gallery', action='index', username=submission.primary_artist.username))}
    </li>
    % endfor
</ul>
% else:
<p> No submissions to list. </p>
% endif
</%def>
