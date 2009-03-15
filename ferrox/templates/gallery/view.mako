<%namespace name="lib" file="/lib.mako"/>
<%namespace name="comments" file="/comments/lib.mako"/>
<%inherit file="base.mako" />

${lib.user_linkbar(c.submission.primary_artist)}

<div class="basic-box">
    <div class="submission-content submission-content-${c.submission.type}">
        % if (c.submission.type == 'video'):
        ${h.embed_flash(h.url_for(controller='gallery', action='file', filename=c.submission.storage_key, id=None))}
        % elif (c.submission.type == 'image'):
        ${h.image_tag(h.url_for(controller='gallery', action='file', filename=c.submission.storage_key, id=None), c.submission.title)}
        % elif (c.submission.type == 'audio'):
        ${h.embed_mp3(h.url_for(controller='gallery', action='file', filename=c.submission.storage_key, id=None))} (Music Submission)
        % elif (c.submission.type == 'text'):
        ${h.HTML.a('Text Submission', href=h.url_for(controller='gallery', action='file', filename=c.submission.storage_key))}, Text submission
        <pre>
        TODO?
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
                ${h.HTML.a('Remove from favorites', href=h.url_for(controller='gallery', action='favorite', id=c.submission.id, username=c.submission.primary_artist.username))}
            % else:
                ${h.HTML.a('Add to favorites', href=h.url_for(controller='gallery', action='favorite', id=c.submission.id, username=c.submission.primary_artist.username))}
            % endif
        % endif
        </div>
        <div class="tags">
        % for tag in c.submission.tags:
            ${tag.text}
        % endfor
        </div>
    </div>
    % for user_submission in c.submission.user_submissions:
    <div class="description">
    <h3> ${lib.user_link(user_submission.user)} </h3>
        ${user_submission.content}
    </div>
    % endfor
</div>

<div class="basic-box">
    <h2>${h.image_tag('/images/icons/h2-comments.png', '')} Comments</h2>
    ${comments.comment_tree(c.submission.discussion.comments, h.url_for(**c.route))}
</div>

<%def name="title()">${c.submission.title} by ${c.submission.primary_artist.display_name}</%def>
