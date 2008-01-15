<%inherit file="base.mako" />

<big><big>${c.submission_title}</big></big><br>
<big>by: ${c.submission_artist}</big><br>
% if (c.submission_type == 'video'):
${h.embed_flash(c.submission_file)}<br>
% elif (c.submission_type == 'image'):
${h.image_tag(c.submission_file,c.submission_title)}<br>
% elif (c.submission_type == 'audio'):
${h.embed_mp3(c.submission_file)} (Music Submission)<br>
% elif (c.submission_type == 'text'):
${h.link_to('Text Submission',c.submission_file)}, Text submission<br>
<pre>
${c.submission_content}
</pre>
% else:
unknown submission type: ${c.submission_type}<br>
% endif
% if (c.submission_halfview):
${h.image_tag(c.submission_halfview,"%s Half View"%c.submission_title)}<br>
% endif
% if (c.submission_thumbnail):
${h.image_tag(c.submission_thumbnail,"%s Thumbnail"%c.submission_title)}<br>
% endif
Description: ${c.submission_description}<br>
Submitted at: ${h.format_time(c.submission_time)}<br><br>

${c.misc}
<%def name="title()">${c.submission_title} by ${c.submission_artist}</%def>

