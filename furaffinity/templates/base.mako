<!DOCTYPE HTML>
<html>
    <head>
        <title>${self.title()} -- Fur Affinity [dot] net</title>
        ${h.stylesheet_link_tag('site.css')}
    </head>
    <body>
        <div id="header">
            <div id="user_header">
                % if not c.auth_user:
                <div id="welcome">Welcome To FurAffinity! Please log in or
                ${h.link_to('register', h.url('register'))}</div>
                <div id="login_header">
                    ${h.form(h.url('/do_login'), method='post')}
                    <span>
                        <label for="username">Username:</label>
                        <span>${h.text_field('username')}</span>
                    </span>
                    <span>
                        <label for="username">Password:</label>
                        <span>${h.password_field('password')}</span>
                    </span>
                    ${h.submit('Login')}
                    ${h.end_form()}
                </div>
                % else: 
                <div id="welcome">Welcome back ${c.auth_user.user_type.sigil}${h.link_to(c.auth_user.display_name, h.url('user', username = c.auth_user.username))}</div>
                <div id="message_header">
                    ${h.form(h.url('/logout'), method='post')}
                    ${h.submit('Logout')}
                    ${h.end_form()}
                </div>
                % endif
            </div>
            <div id="nav_header">
                <h1 id="logo">${h.image_tag('header.jpg', 'FurAffinity')}</h1>
                <div id="nav_bar">
                    <div id="nav">
                        <ul>
                            <li>${h.link_to("Submit Art", h.url('submit_art'))}</li>
                            <li>${h.link_to("Browse", h.url('browse'))}</li>
                            <li>${h.link_to("Forums", 'http://www.furaffinityforums.net')}</li>
                            <li>${h.link_to("Chat", 'http://www.wikiffinity.net/index.php?title=IRC_Chat')}</li>
                            <li>${h.link_to("Journal", h.url('journal'))}</li>
                            <li>${h.link_to("Support", 'http://www.wikiffinity.net/')}</li>
                            <li>${h.link_to("Staff", h.url('staff'))}</li>
                        </ul>
                        <div id="search">
                            ${h.form(h.url(controller='search', action='search'), method='post')}
                            <span>
                                <label for="search">Search:</label>
                                <span>${h.text_field('search')}</span>
                            </span>
                            ${h.submit('Search')}
                            ${h.end_form()}
                        </div>
                    </div>
                    <ul id="control_panels">
                        % if c.auth_user:
                        <li>${h.link_to("Control Panel", h.url('control_panel'))}</li>
                        % if c.auth_user.is_admin():
                        <li>${h.link_to("Admin Control Panel", h.url('administration'))}</li>
                        % endif
                        % endif
                        % if not c.auth_user:
                        <li>${h.link_to("Lost Password", h.url('lost_password'))}</li>
                        % endif
                    </ul>
                </div>
            </div>
            <div id="banner_ad">
                ${h.image_tag('bannerad.jpg', 'Ad')}
            </div>
        </div>

        % if c.error_msg:
        <div style="background-color: darkred;">${c.error_msg}</div>
        % endif

        <div id="body">
            ${next.body()}
        </div>

        <div id="footer">
        </div>
    </body>
</html>
