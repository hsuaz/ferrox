<%namespace name="lib" file="/lib.mako"/>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <title>${self.title()} -- Fur Affinity [dot] net</title>
    <link rel="shortcut icon" type="image/png" href="/images/icons/pawprint.png"/>
    ${self.css_links()}
    ${self.javascript_includes()}
</head>
<body>
<p id="skip-to-content"><a href="#content">Skip to content</a></p>
<div id="header">
    <div id="user">
        % if c.auth_user.id == 0:
        <p>
            Welcome to FurAffinity! Please log in or
            ${h.link_to('register', h.url(controller='index', action='register'))}.
        </p>
        <p>(${h.link_to("Lost your password?", h.url(controller='index', action='lost_password'))})</p>
        ${h.form(h.url(controller='index', action='login_check'), method='post')}
        <dl class="standard-form">
            <dt>Username</dt>
            <dd>${h.text_field('username')}</dd>
            <dt>Password</dt>
            <dd>${h.password_field('password')}</dd>
        </dl>
        ${h.submit('Login')}
        ${h.end_form()}
        % else:
        ${h.form(h.url(controller='index', action='logout'), method='post')}
        <p>Welcome back, ${lib.user_link(c.auth_user)}!  ${h.submit('Log out')}</p>
        ${h.end_form()}
        <ul class="inline">
            <li>${h.link_to("Profile", h.url(controller='user', action='view', username=c.auth_user.username))}</li>
            <li>${h.link_to("Journal", h.url(controller='journal', action='index', username=c.auth_user.username))}</li>
            <li>${h.link_to("Gallery", h.url(controller='gallery', action='user_index', username=c.auth_user.username))}</li>
        </ul>
        <ul class="inline">
            <li>${h.link_to("Settings", h.url(controller='user', action='settings', username=c.auth_user.username))}</li>
            <li>${h.link_to("Submit Art", h.url(controller='gallery', action='submit', username=c.auth_user.username))}</li>
        </ul>
        % if c.auth_user.can('administrate'):
        <p id="superpowers">${h.link_to("Activate Superpowers", h.url(controller='admin'), class_='admin')}</p>
        % endif
        <ul id="messages" class="FINISHME">
            <li class="new"> ${h.link_to(h.image_tag('/images/icons/internet-mail.png', '') + "1 new note", h.url(controller='notes', action='user_index', username=c.auth_user.username))} </li>
            <li class="new"> ${h.link_to(h.image_tag('/images/icons/internet-group-chat.png', '') + "5 new feedback", "")} </li>
            <li> ${h.link_to(h.image_tag('/images/icons/internet-news-reader.png', '') + "No new watches", "")} </li>
        </ul>
        % endif
    </div>
    <h1 id="logo">${h.link_to(h.image_tag('/images/banner.jpg', 'FurAffinity'), h.url(controller='index', action='index'))}</h1>
</div>
<div id="navigation">
    <div class="basic-box" id="site-nav">
        <h2>Site</h2>
        <ul>
            <li>${h.link_to("Home", h.url(controller='index', action='index'))}</li>
            <li>${h.link_to("Browse", h.url(controller='gallery', action='index'))}</li>
            <li>${h.link_to("News", h.url(controller='news'))}</li>
            <li>${h.link_to("Staff", h.url(controller='staff'))}</li>
        </ul>
    </div>
    <div class="basic-box" id="community-nav">
        <h2>Community</h2>
        <ul>
            <li>${h.link_to("Forums", 'http://www.furaffinityforums.net')}</li>
            <li>${h.link_to("Chat", 'http://www.wikiffinity.net/index.php?title=IRC_Chat')}</li>
            <li>${h.link_to("Support", 'http://www.wikiffinity.net/')}</li>
        </ul>
    </div>
    <div class="basic-box" id="search">
        <h2>Search gallery</h2>
        ${h.form(h.url(controller='search', action='search'), method='post')}
        <p>
            ${h.text_field('search')}
            ${h.submit('Search')}
        </p>
        ${h.end_form()}
    </div>
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

<div id="footer">
    <div id="shameless-whoring">
        <img src="http://static.furaffinity.net/images/donate.gif" alt="Screw the ads and donate!"/>
    </div>
    <ul class="inline">
        <li><a href="/.ferrox/design/docs/tos">Terms of Service</a></li>
        <li><a href="/.ferrox/design/docs/sa">Submission Agreement</a></li>
        <li><a href="/.ferrox/design/docs/aup">Acceptable Upload Policy</a></li>
    </ul>
    <p> No portions of furaffinity.net may be used without expressed, written permission. </p>
    <p> All artwork is copyrighted to the respective owner.  All rights reserved unless otherwise specified. </p>
    <div id="stats">
        <div id="python-bar" style="width: 37%;">&nbsp;</div>
        <p> Page generated in 0.425s; 37% SQL, 4 queries </p>
    </div>
</div>
</body>
</html>

<%def name="css_links()">
    <link rel="stylesheet" type="text/css" href="${h.url_for(controller='stylesheets', action='index', sheet='reset')}"/>
    <link rel="stylesheet" type="text/css" href="${h.url_for(controller='stylesheets', action='index', sheet='common')}"/>
    <link rel="stylesheet" type="text/css" href="${h.url_for(controller='stylesheets', action='index', sheet=c.auth_user.preference('style_sheet'), color=c.auth_user.preference('style_color'))}"/>
</%def>

<%def name="javascript_includes()">
    ${h.javascript_include_tag("jquery-1.2.1.pack.js")}
    % if hasattr(c, 'javascripts'):
    % for script in c.javascripts:
    ${h.javascript_include_tag("%s.js" % script)}
    % endfor
    % endif
</%def>
