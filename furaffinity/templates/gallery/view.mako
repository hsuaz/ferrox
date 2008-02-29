<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div class="basic-box FINISHME">
    <h2>${c.submission.title}</h2>

    <div class="time">Submitted on ${h.format_time(c.submission.time)}</div>
    <div class="artist FINISHME">by ${lib.user_link(c.submission.primary_artist)}</div>
    <div class="buttons FINISHME">buttons here lol</div>
    <div class="tags FINISHME">${c.tags}</div>
    <div class="content">
        % if (c.submission.type == 'video'):
        ${h.embed_flash(c.submission.file)}<br>
        % elif (c.submission.type == 'image'):
        ${h.image_tag(c.submission_file, c.submission.title)}<br>
        % elif (c.submission.type == 'audio'):
        ${h.embed_mp3(c.submission_file)} (Music Submission)<br>
        % elif (c.submission.type == 'text'):
        ${h.link_to('Text Submission', c.submission_file)}, Text submission<br>
        <pre>
        ${c.submission.description_parsed}
        </pre>
        % else:
        unknown submission type: ${c.submission_type}<br>
        % endif
    </div>
    <div class="description">
        ${c.submission.description}
    </div>

<%def name="title()">${c.submission.title} by ${c.submission.user_submission[0].user.display_name}</%def>
