<%namespace name="lib" file="/lib.mako"/>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <title>${self.title()} -- ${c.site_name}</title>
    <link rel="shortcut icon" type="image/png" href="/images/icons/favicon.png"/>
    ${self.css_links()}
    ${self.javascript_includes()}
</head>
<body>
<p id="skip-to-content"><a href="#content">Skip to content</a></p>
<div id="header">
    <div id="user">
        % if c.auth_user.id == 0:
        <p>
            Welcome to ${c.site_name}! Please log in or
            ${h.link_to('register', h.url_for(controller='index', action='register'))}.
        </p>
        ## DISABLED DUE TO MISSING ROUTE
        ## <p>(${h.link_to("Lost your password?", h.url_for(controller='index', action='lost_password'))})</p>
        ${c.empty_form.start(h.url_for(controller='index', action='login_check'), method='post')}
        <dl class="standard-form">
            <dt>Username</dt>
            <dd>${c.empty_form.text_field('username')}</dd>
            <dt>Password</dt>
            <dd>${c.empty_form.password_field('password')}</dd>
        </dl>
        ${c.empty_form.submit('Login')}
        ${c.empty_form.end()}
        % else:
        <div id="user-links">
            <ul>
                <li>${h.link_to("%s Settings" % h.image_tag('/images/icons/link-settings.png', ''), h.url_for(controller='user_settings', action='index', username=c.auth_user.username))}</li>
                <li>${h.link_to("%s Upload" % h.image_tag('/images/icons/link-upload.png', ''), h.url_for(controller='gallery', action='submit', username=c.auth_user.username))}</li>
                <li>${h.link_to("%s Write" % h.image_tag('/images/icons/link-write.png', ''), h.url_for(controller='journal', action='post', username=c.auth_user.username))}</li>
                <li>${h.link_to("%s Watchstream" % h.image_tag('/images/icons/link-watchstream.png', ''), h.url_for(controller='gallery', action='watchstream', username=c.auth_user.username))}</li>
            </ul>
            <ul>
                <% note_count = c.auth_user.unread_note_count() %>
                <li${' class="new"' if note_count else ''}> ${h.link_to("%s %d new note%s" % (h.image_tag('/images/icons/link-notes.png', ''), note_count, 's' if note_count != 1 else ''), h.url_for(controller='notes', action='user_index', username=c.auth_user.username))} </li>
                <li class="new TODO"> ${h.link_to(h.image_tag('/images/icons/link-comments.png', '') + " 25 comments", "")} </li>
                <li class="new TODO"> ${h.link_to(h.image_tag('/images/icons/link-messages.png', '') + " 124 other", "")} </li>
            </ul>
        </div>
        <div id="user-info">
            ${c.empty_form.start(h.url_for(controller='index', action='logout'), method='post')}
            <p>${lib.user_link(c.auth_user)}</p>
            <p id="user-avatar">${h.image_tag(h.get_avatar_url(), '[default avatar]')}</p>
            <p>${c.empty_form.submit('Log out', class_='small')}</p>
            ${c.empty_form.end()}
        </div>
        % endif
    </div>
    <h1 id="banner">${h.image_tag('/images/banner.png', '')}</h1>
    <h1 id="logo">${h.image_tag('/images/logo.png', 'FurAffinity')}</h1>
    ${c.empty_form.start(h.url_for(controller='search', action='do'), method='post', id='search')}
    <p>
        ${c.empty_form.text_field('query_main', class_='search')}
        ${c.empty_form.submit('Search')}
    </p>
    ${c.empty_form.end()}
    <ul id="main-navigation">
        <li>${h.link_to("%s Browse" % h.image_tag('/images/icons/link-browse.png', ''), h.url_for(controller='gallery', action='index'))}</li>
        <li>${h.link_to("%s Forum" % h.image_tag('/images/icons/link-forum.png', ''), 'http://www.furaffinityforums.net')}</li>
        <li>${h.link_to("%s News" % h.image_tag('/images/icons/link-news.png', ''), h.url_for(controller='news', action='index'))}</li>
        <li>${h.link_to("%s Support" % h.image_tag('/images/icons/link-wiki.png', ''), 'http://www.wikiffinity.net/')}</li>
        ## DISABLED DUE TO MISSING ROUTE
        ##<li>${h.link_to("%s Staff" % h.image_tag('/images/icons/link-staff.png', ''), h.url_for(controller='staff', action='index'))}</li>
        % if c.auth_user.can('admin.auth'):
        <li id="superpowers">${h.link_to("%s Activate Superpowers" % h.image_tag('/images/icons/link-admin.png', ''), h.url_for(controller='admin', action='auth'), id='admin')}</li>
        % endif
    </ul>
    <div id="css-shadow"></div>
</div>

<ul id="ads">
    <li>${h.image_tag('/images/ad1.gif', 'Ad 1')}</li>
    <li>${h.image_tag('/images/ad2.gif', 'Ad 2')}</li>
</ul>

% if c.error_msgs:
<ul id="error">
    asdfsadf
    % for error in c.error_msgs:
    <li>${error}</li>
    % endfor
</ul>
% endif

<div id="content">
    ${next.body()}
</div>

<div id="static-footer-ad">
    ${h.image_tag('http://servbot.furaffinity.net/www/images/cs_base.jpg')}
</div>

<div id="footer">
    <div id="shameless-whoring">
        <img src="http://static.furaffinity.net/images/donate.gif" alt="Screw the ads and donate!"/>
    </div>
    <ul class="inline">
        <li><a href="/.ferrox/design/docs/tos">Terms of Service</a></li>
        <li><a href="/.ferrox/design/docs/sa">Submission Agreement</a></li>
        <li><a href="/.ferrox/design/docs/aup">Acceptable Upload Policy</a></li>
    </ul>
    <p> All artwork is copyrighted to the respective owner.  All rights reserved unless otherwise specified. </p>
    <p> Icons belong to <a href="http://www.pinvoke.com/">Yusuke Kamiyamane</a>
        and are licensed under <a href="http://creativecommons.org/licenses/by/3.0/">CC-A 3.0</a>. </p>
    <div id="stats">
<%
    total_time = c.time_elapsed()
    sql_time = c.query_log.time_elapsed()
    sql_percent = sql_time / total_time * 100
%>
        <p> Page generated in ${"%.4f" % total_time}s; ${"%.1f" % sql_percent}% SQL, ${len(c.query_log.queries)} quer${'y' if len(c.query_log.queries) == 1 else 'ies'} </p>
        <div id="stats-bar">
            <div id="stats-bar-python" style="width: ${(total_time - sql_time) / 0.05}em;"></div>
            <div id="stats-bar-sql" style="width: ${sql_time / 0.05}em;"></div>
        </div>
    </div>
    % if c.auth_user.can('debug'):
    <table id="query-log">
    <tr>
        <th>Time</th>
        <th>Query</th>
    </tr>
    % for query, time in sorted(c.query_log.queries, key=lambda x: x[1], reverse=True):
    <tr>
        <td>${"%.6f" % time}</td>
        <td>${query}</td>
    </tr>
    % endfor
    </table>
    % endif
</div>
</body>
</html>

<%def name="css_links()">
    <link rel="stylesheet" type="text/css" href="/stylesheets/reset.css"/>
    <link rel="stylesheet" type="text/css" href="/stylesheets/powder/common.css"/>
</%def>

<%def name="javascript_includes()">
    % for script in c.javascripts:
    ${h.javascript_include_tag("%s.js" % script)}
    % endfor
</%def>
