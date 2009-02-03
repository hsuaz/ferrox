<%namespace name="lib" file="/lib.mako"/>
<%namespace name="comments" file="/comments/lib.mako"/>
<%inherit file="base.mako" />

${lib.user_linkbar(c.submission.primary_artist)}

<div class="basic-box">
    <h2>${c.submission.title}</h2>

    <div class="submission-content submission-content-${c.submission.type}">
        % if (c.submission.type == 'video'):
        ${h.embed_flash(h.url_for(controller='gallery', action='file', filename=c.submission.mogile_key, id=None))}
        % elif (c.submission.type == 'image'):
        ${h.image_tag(h.url_for(controller='gallery', action='file', filename=c.submission.mogile_key, id=None), c.submission.title)}
        % elif (c.submission.type == 'audio'):
        ${h.embed_mp3(h.url_for(controller='gallery', action='file', filename=c.submission.mogile_key, id=None))} (Music Submission)
        % elif (c.submission.type == 'text'):
        ${h.link_to('Text Submission', h.url_for(controller='gallery', action='file', filename=c.submission.mogile_key))}, Text submission
        <pre>
        ${c.submission.message.content}
        </pre>
        % else:
        unknown submission type: ${c.submission_type}
        % endif
    </div>
    <div class="metadata">
        <div class="time">Submitted on ${h.format_time(c.submission.time)}</div>
        <div class="buttons">
        % if c.auth_user:
            % if c.submission in c.auth_user.favorite_submissions:
                ${h.link_to('Remove from favorites', h.url_for(controller='gallery', action='favorite', id=c.submission.id, username=c.submission.primary_artist.username))}
            % else:
                ${h.link_to('Add to favorites', h.url_for(controller='gallery', action='favorite', id=c.submission.id, username=c.submission.primary_artist.username))}
            % endif
        % endif
        </div>
        <div class="tags">
        % for tag in c.submission.tags:
            ${tag.text}
        % endfor
        </div>
    </div>
    <div class="description">
    <h3> durp durp </h3>
        ${c.submission.message.content}
    </div>
</div>

${comments.comment_tree(c.submission.discussion.comments, h.url_for(**c.route))}

<%def name="title()">${c.submission.title} by ${c.submission.primary_artist.display_name}</%def>
