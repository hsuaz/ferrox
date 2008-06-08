<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${lib.user_linkbar(c.user)}

<div class="basicbox">
${c.empty_form.start(h.url(controller='user', action='avatar_update', username=c.user.username), multipart=True)}
% if c.user.default_avatar:
    <p>Default Avatar: ${c.user.default_avatar.title}</p>
% endif
% if c.user.avatars:
<ul>
    % for av in c.user.avatars:
        <li class="basicbox" style="float: left">
            ${av.title}<br>
            ${h.image_tag(h.url_for(controller='gallery', action='file', filename=av.mogile_key), av.title)}<br>
            Delete? ${c.empty_form.check_box("delete_%d"%av.id)}<br>
            Default: ${c.empty_form.radio_button("default", av.id, checked=av.default)}
        </li>
    % endfor
</ul>
% else:
    <p>No avatars!</p>
% endif
<dl class="standard-form">
<dt>Upload new avatar:</dt>
<dd>${c.empty_form.file_field('newavatar')}</dd>
<dt>Title</dt>
<dd>${c.empty_form.text_field('newavatar_title')}</dd>
<dt>Make new avatar your default.</dt>
<dd>Default: ${c.empty_form.radio_button("default", 0, checked=(True if not c.user.default_avatar else False))}</dd>
</dl>
</p>
${c.empty_form.submit('Update Avatars')}
${c.empty_form.end()}
</div>

<%def name="title()">${c.user.display_name}</%def>
