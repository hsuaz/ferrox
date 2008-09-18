<div class="userlink-popup">
    <img src="/images/foxy.gif" alt="" class="avatar"/>
    <div class="name">${c.user.role.sigil}${c.user.display_name}</div>
    <div class="role">${c.user.role.name}</div>
    % if c.your_friend and c.friend_of:
    <div class="rel">Mutual friend</div>
    % elif c.friend_of:
    <div class="rel">Has you friended</div>
    % elif c.your_friend:
    <div class="rel">Is your friend</div>
    % endif
    % if c.blocking and c.blocked_by:
    <div class="rel rel-blocked">Mutually blocked</div>
    % elif c.blocked_by:
    <div class="rel rel-blocked">Has you blocked</div>
    % elif c.blocking:
    <div class="rel rel-blocked">Is blocked</div>
    % endif
    <ul class="links inline">
        <li><a href="${h.url_for(controller='user', action='view', username=c.user.username)}">Profile</a></li>
        <li><a href="${h.url_for(controller='gallery', action='index', username=c.user.username)}">Gallery</a></li>
        <li><a href="${h.url_for(controller='journal', action='index', username=c.user.username)}">Journal</a></li>
    </ul>
    % if c.user.is_online():
    <div class="online">online</div>
    % else:
    <div class="offline">offline</div>
    % endif
</div>
