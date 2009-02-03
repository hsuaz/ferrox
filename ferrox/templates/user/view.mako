<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${lib.user_linkbar(c.user)}

<div class="columns-left">
<div class="basic-box TODO">
    <h2>${h.image_tag('/images/icons/h2-featured.png', '')} Featured</h2>

    % if not len(c.recent_submissions):
    <p>No featured submissions</p>
    % else:
    <div class="latest-submission">
        <h3>${c.recent_submissions[0].title}</h3>
        <p class="timestamp">${h.format_time(c.recent_submissions[0].time)}</p>
        <div class="halfview">${h.link_to(h.image_tag(h.url_for(controller='gallery', action='file', filename=c.recent_submissions[0].halfview.mogile_key), c.recent_submissions[0].title), h.url_for(controller='gallery', action='view', id=c.recent_submissions[0].id, username=c.user.username))}</div>
        <div class="description">${c.recent_submissions[0].content}</div>
        <ul class="inline admin">
            <li>${h.link_to("%s Edit" % h.image_tag('/images/icons/link-edit.png', ''), h.url_for(controller='gallery', action='edit', id=c.recent_submissions[0].id, username=c.user.username), class_='button admin')}</li>
        </ul>
        <ul class="inline links">
            <li>${h.link_to("%s XXX comments" % h.image_tag('/images/icons/link-comments.png', ''), h.url_for(controller='gallery', action='view', id=c.recent_submissions[0].id, username=c.user.username), class_='button TODO')}</li>
        </ul>
    </div>

    <ul class="thumbnail-row">
        % for submission in c.recent_submissions[1:]:
        <li>${h.link_to(h.image_tag(h.url_for(controller='gallery', action='file', filename=submission.thumbnail.mogile_key), submission.title), h.url_for(controller='gallery', action='view', id=submission.id, username=c.user.username))}</li>
        % endfor
    </ul>
    ${h.link_to('Browse featured works', h.url_for(controller='gallery', action='index', username=c.user.username), class_='button TODO')}
    % endif
</div>
<div class="basic-box">
    <h2>${h.image_tag('/images/icons/h2-gallery.png', '')} Gallery</h2>

    % if not len(c.recent_submissions):
    <p>No submissions</p>
    % else:
    <div class="latest-submission">
        <h3>${c.recent_submissions[0].title}</h3>
        <p class="timestamp">${h.format_time(c.recent_submissions[0].time)}</p>
        <div class="halfview">${h.link_to(h.image_tag(h.url_for(controller='gallery', action='file', filename=c.recent_submissions[0].halfview.mogile_key), c.recent_submissions[0].title), h.url_for(controller='gallery', action='view', id=c.recent_submissions[0].id, username=c.user.username))}</div>
        <div class="description">${c.recent_submissions[0].content}</div>
        <ul class="inline admin">
            <li>${h.link_to("%s Edit" % h.image_tag('/images/icons/link-edit.png', ''), h.url_for(controller='gallery', action='edit', id=c.recent_submissions[0].id, username=c.user.username), class_='button admin')}</li>
        </ul>
        <ul class="inline links">
            <li>${h.link_to("%s XXX comments" % h.image_tag('/images/icons/link-comments.png', ''), h.url_for(controller='gallery', action='view', id=c.recent_submissions[0].id, username=c.user.username), class_='button TODO')}</li>
        </ul>
    </div>

    <ul class="thumbnail-row">
        % for submission in c.recent_submissions[1:]:
        <li>${h.link_to(h.image_tag(h.url_for(controller='gallery', action='file', filename=submission.thumbnail.mogile_key), submission.title), h.url_for(controller='gallery', action='view', id=submission.id, username=c.user.username))}</li>
        % endfor
    </ul>
    ${h.link_to('Browse gallery', h.url_for(controller='gallery', action='index', username=c.user.username), class_='button')}
    % endif
</div>
</div>
<div class="columns-right">
<div class="basic-box">
    <h2>${h.image_tag('/images/icons/h2-journal.png', '')} Journal</h2>

    % if not len(c.recent_journals):
    <p>No journals.</p>
    % else:
    <div class="latest-journal">
        <h3>${c.recent_journals[0].title}</h3>
        <p class="timestamp">${h.format_time(c.recent_journals[0].time)}</p>
        <div class="message TODO">
            ${c.recent_journals[0].content_parsed}
        </div>
        <ul class="inline admin">
            <li>${h.link_to("%s Edit" % h.image_tag('/images/icons/link-edit.png', ''), h.url_for(controller='journal', action='edit', id=c.recent_journals[0].id, year=c.recent_journals[0].time.year, month=c.recent_journals[0].time.month, day=c.recent_journals[0].time.day, username=c.user.username), class_='button admin')}</li>
        </ul>
        <ul class="inline links">
            <li>${h.link_to("%s %d comments" % (h.image_tag('/images/icons/link-comments.png', ''), c.recent_journals[0].discussion.comment_count), h.url_for(controller='journal', action='view', id=c.recent_journals[0].id, year=c.recent_journals[0].time.year, month=c.recent_journals[0].time.month, day=c.recent_journals[0].time.day, username=c.user.username), class_='button')}</li>
        </ul>
    </div>

    <ul class="recent-journals">
        % for journal_entry in c.recent_journals[1:]:
        <li>
            <div class="timestamp">${h.format_time(journal_entry.time)}</div>
            <div class="title">${h.link_to(journal_entry.title, h.url_for(controller='journal', action='view', id=journal_entry.id, year=journal_entry.time.year, month=journal_entry.time.month, day=journal_entry.time.day, username=c.user.username))}</div>
        </li>
        % endfor
    </ul>
    % endif
</div>
<div class="basic-box TODO">
    <h2>${h.image_tag('/images/icons/h2-shouts.png', '')} Shouts</h2>

    <ul class="shoutbox">
        <li>
            <div class="avatar">${h.image_tag(h.get_avatar_url(), '')}</div>
            <div class="header">
                ${lib.user_link(c.auth_user)}
                <span class="timestamp">time</span>
            </div>
            <div class="message">
                message goes here, but this aint done yet
            </div>
        </li>
        <li>
            <div class="avatar">${h.image_tag(h.get_avatar_url(), '')}</div>
            <div class="header">
                ${lib.user_link(c.auth_user)}
                <span class="timestamp">time</span>
            </div>
            <div class="message">
                message goes here, but this aint done yet
            </div>
        </li>
        <li>
            <div class="avatar">${h.image_tag(h.get_avatar_url(), '')}</div>
            <div class="header">
                ${lib.user_link(c.auth_user)}
                <span class="timestamp">time</span>
            </div>
            <div class="message">
                Quisque massa tellus, venenatis nec, vestibulum ut, dictum sed, nisi. Maecenas sollicitudin nulla quis dolor. Integer adipiscing bibendum turpis. Sed scelerisque, neque non egestas luctus, nisi magna condimentum dui, non blandit velit nunc id erat. In nec nunc ut leo tincidunt dapibus. Nullam eros. Nulla facilisi. Praesent gravida dui in arcu pulvinar fermentum. Phasellus pretium. Sed fermentum porttitor tortor. 
            </div>
        </li>
    </ul>
</div>
</div>

<%def name="title()">${c.user.display_name}</%def>
