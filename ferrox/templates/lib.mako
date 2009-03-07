<%def name="news_entry(entry, short)">
<%
    if entry.is_deleted:
        if not c.auth_user.can('admin.auth'):
            return ''
        extra_class = ' deleted'
    else:
        extra_class = ''
%>
<div class="entry${extra_class}">
    <div class="header">
        <div class="avatar">
            % if not entry.is_anonymous:
            ${h.image_tag(h.get_avatar_url(entry), entry.user.username)}
            % else:
            <img src="${h.get_avatar_url()}" alt="default avatar"/>
            % endif
        </div>
        <%
            if entry.is_anonymous:
                author_string = 'Staff'
            else:
                author_string = capture(user_link, entry.user)
        %>
        <div class="author">${author_string}</div>
        <h3>${h.HTML.a(entry.title, href=h.url_for(controller='news', action='view', id=entry.id))}</h3>
        <div class="date">${h.format_time(entry.time)}</div>
    </div>
    <div class="message">
        % if short:
            ${entry.content_short}
        % else:
            ${entry.content_parsed}
        % endif
    </div>
    % if c.auth_user.can('admin.auth'):
    ${c.empty_form.start(h.url_for(controller='news', action='edit', id=entry.id), method='post')}
    <ul class="inline admin actions">
        <li>${h.HTML.a(h.image_tag('/images/icons/link-edit.png', ''), ' Edit', href=h.url_for(controller='news', action='edit', id=entry.id), class_='button admin')}</li>
        % if entry.is_deleted:
        <li>${c.empty_form.submit('Undelete')}</li>
        % else:
        <li>${c.empty_form.submit("%s Delete" % h.image_tag('/images/icons/link-edit.png', ''), class_='admin')}</li>
        % endif
    </ul>
    ${c.empty_form.end()}
    % endif

<% news_url = h.url_for(controller='news', action='view', id=entry.id) %>
    <ul class="inline actions">
        <li>${h.HTML.a(h.image_tag('/images/icons/link-comments.png', ''), ' View comments', href=h.url_for(controller='comments', action='view', post_url=news_url), class_='button')}</li>
        <li>${h.HTML.a(h.image_tag('/images/icons/link-reply.png', ''), ' Reply', href=h.url_for(controller='comments', action='reply', post_url=news_url), class_='button')}</li>
    </ul>
</div>
</%def>

<%def name="journal_entry(entry, short)">
<%
    if entry.status == 'deleted':
        if not c.auth_user.can('admin.auth'):
            return ''
        extra_class = ' deleted'
    else:
        extra_class = ''
%>
<div class="entry${extra_class}">
    <div class="header">
        <div class="avatar FINISHME"><img src="http://a.furaffinity.net/${entry.user.username}.gif" alt="avatar"/></div>
        <div class="author">
            ${user_link(entry.user)}
        </div>
        <h3>${h.HTML.a(entry.title, href=h.url_for(controller='journal', action='view', username=entry.user.username, year=entry.time.year, month=entry.time.month, day=entry.time.day, id=entry.id))}</h3>
        <div class="date">${h.format_time(entry.time)}</div>
        % if c.auth_user.can('admin.auth'):
        ${c.empty_form.start(h.url_for(controller='journal', action='edit', username=entry.user.username, year=entry.time.year, month=entry.time.month, day=entry.time.day, id=entry.id), method='post')}
        <ul class="inline admin actions">
            <li>${h.HTML.a(h.image_tag('/images/icons/link-edit.png', ''), ' Edit', href=h.url_for(controller='journal', action='edit', username=entry.user.username, year=entry.time.year, month=entry.time.month, day=entry.time.day, id=entry.id), class_='button admin')}</li>
            % if entry.status == 'deleted':
            <li>${c.empty_form.submit('Undelete')}</li>
            % else:
            <li>${c.empty_form.submit("%s Delete" % h.image_tag('/images/icons/link-edit.png', ''), class_='admin')}</li>
            % endif
        </ul>
        ${c.empty_form.end()}
        % endif
    </div>
    <div class="message">
        % if short:
            ${entry.content_short}
        % else:
            ${entry.content_parsed}
        % endif
    </div>
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
        <div class="title">${note.title}${icon}</div>
        <div class="avatar">${h.image_tag(h.get_avatar_url(owner), owner.display_name)}</div>
        % if note.sender == owner:
        <div class="author">${h.image_tag('/images/icons/go-next.png', 'Sent to')} ${user_link(note.recipient)}</div>
        % else:
        <div class="author">${h.image_tag('/images/icons/go-previous.png', 'Received from')} ${user_link(note.sender)}</div>
        % endif
        <div class="date">Date: ${h.format_time(note.time)}</div>
    </div>
    <ul class="micro-linkbar">
        <li>${h.HTML.a(h.image_tag('/images/icons/mail-reply-sender.png', ''), ' Reply', href=h.url_for(controller='notes', action='reply', username=c.route['username'], id=note.id))}</li>
        <li>${h.HTML.a(h.image_tag('/images/icons/mail-forward.png', ''), ' Forward', href=h.url_for(controller='notes', action='forward', username=c.route['username'], id=note.id))}</li>
    </ul>
    <div class="content">
        ${note.content_parsed}
    </div>
</div>
</%def>

<%def name="note_collapsed_entry(note, owner)">
<div class="entry collapsed">
    <div class="header">
        <div class="title">${h.HTML.a(note.title, href=h.url_for(controller='notes', action='view', username=owner.username, id=note.id), class_='js-expand-note')}</div>
    </div>
</div>
</%def>

<%def name="user_link(user, care_about_online=True)">
<span class="userlink">
    <a href="${h.url_for(controller='user', action='view', username=user.username)}" class="js-userlink-target">${user.role.sigil}${user.username}</a>
</span>
</%def>

<%def name="user_linkbar(user)">
<div id="user-header">
    ${h.image_tag(h.get_avatar_url(), '[default avatar]', class_='avatar TODO')}
    <div id="user-header-name">
        <span id="user-header-name-handle">${user.role.sigil}${user.display_name}</span>
        <span id="user-header-name-alias" class="TODO">aka..  Eevee?</span>
    </div>
    <div id="user-header-actions">
        % if c.auth_user:
        <%
            # Add one icon per relationship to the link
            relationship_images = []
            for rel in ('friend', 'watching_submissions', 'watching_journals',
                        'blocked'):
                if c.auth_user.get_relationship(user, rel):
                    img = h.image_tag('/images/icons/rel-%s.png' % rel, rel)
                else:
                    img = h.image_tag('/images/icons/rel-%s-off.png' % rel,
                                      'not %s' % rel)
                relationship_images.append(img)

            # Lastly, text label
            relationship_images.append('Relationships')
        %>
        ${h.HTML.a(
            href=h.url_for(controller='user_settings', action='relationships', username=c.auth_user.username, other_user=user.username), \
            class_='TODO button',
            *relationship_images)}
        ${h.HTML.a(h.image_tag('/images/icons/link-user-note.png', ''), 'Send note', href=h.url_for(controller='notes', action='write', username=c.auth_user.username, recipient=user.username), class_='button')}
        % endif
    </div>
    <ul class="tab-bar">
        % for title, image, route in ('Dash',            'recent',      dict(controller='user', action='view')), \
                                     ('Profile',         'profile',     dict(controller='user', action='profile')), \
                                     ('Commissions',     'commissions', dict(controller='user', action='commissions')), \
                                     ('Journal',         'journal',     dict(controller='journal', action='index')), \
                                     ('Gallery',         'gallery',     dict(controller='gallery', action='index')):
        <%
            # XXX this might be too magical
            if c.route['controller'] == route['controller'] and \
               c.route['action'] == route['action']:
                class_ = 'you-are-here'
            elif c.route['controller'] == route['controller'] and \
                 c.route['controller'] in ('gallery', 'journal'):
                class_ = 'you-are-here'
            else:
                class_ = ''
        %>
        <li>${h.HTML.a(h.image_tag('/images/icons/link-user-%s.png' % image, ''), title, href=h.url_for(username=user.username, **route), class_=class_)}</li>
        % endfor
    </ul>
    <div class="sub-bar-thing"> more stuff here yeah</div>
</div>
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
<!-- comment to remove intervening whitespace
    % for submission in submissions:
    --><li id="sub${submission.id}">
        <a href="${h.url_for(controller='gallery', action='view', id=submission.id, username=submission.primary_artist.username)}">
        % if submission.thumbnail:
        <span class="thumbnail">${h.image_tag(h.url_for(controller='gallery', action='file', filename=submission.thumbnail.mogile_key), submission.title)}</span>
        % endif
        <span class="title">${submission.title}</span>
        </a>
    </li><!--
    % endfor
-->
</ul>
% else:
<p> No submissions to list. </p>
% endif
</%def>
