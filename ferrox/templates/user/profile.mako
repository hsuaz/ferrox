<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${lib.user_linkbar(c.user)}

<div class="lr-left">
<div class="basic-box">
    <h2> Profile </h2>
    <dl class="two-column-list">
        <dt>User</dt>
        <dd>${h.link_to(c.user.display_name, h.url_for(controller='user', action='view', username=c.user.username))} (${c.user.id})</dd>
        % for datum in [u'artist_type', u'bio', u'location', u'interests', \
                        u'occupation', u'age', u'nerd_shell', u'nerd_os', \
                        u'nerd_browser']:
        <dt>${c.user.metadatum(datum)['description']}</dt>
        <dd>${c.user.metadatum(datum)['value']}</dd>
        % endfor
    </dl>
</div>
</div>

<div class="lr-right">
<div class="basic-box FINISHME">
    <h2> Contact </h2>
    <p> Not implemented yet; needs some thought; probably shouldn't go here either since bio can be pretty epic huge </p>
</div>
</div>

<div class="float-clear-hack"></div>

<div class="lr-left">
<div class="basic-box">
    <h2> A few of my favorite things </h2>
    <dl class="two-column-list">
        % for datum in [u'fav_quote', u'fav_movie', u'fav_game', \
                        u'fav_player', u'fav_artist', u'fav_animal', \
                        u'fav_site', u'fav_food']:
        <dt>${c.user.metadatum(datum)['description']}</dt>
        <dd>${c.user.metadatum(datum)['value']}</dd>
        % endfor
    </dl>
</div>
</div>

<div class="lr-right">
<div class="basic-box FINISHME">
    <h2> Intentionally left blank </h2>
    <p> Figure out what other profile fields we want and arrange as appropriate. </p>
</div>
</div>

<%def name="title()">${c.user.display_name}'s Profile</%def>
