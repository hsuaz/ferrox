<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

<div class="basic-box">
    <h2>${title()}
    % if c.paging_links:
        ${c.empty_form.start(h.implicit_url_for(), method='post')}
        ${c.empty_form.hidden_field('perpage')}
        % for link in c.paging_links:
            % if link[0] == '...':
                ${link[1]}
            % elif link[0] == 'submit':
                ${c.empty_form.submit(value=link[1], name='page')}
            % else:
                ${c.empty_form.submit(value=link[1], name='page', disabled_='disabled')}
            % endif
        % endfor
        ${c.empty_form.end()}
    % endif
    </h2>
    <ul>
    % for u in c.users:
        <li>${lib.user_link(u, False)} </li>
    % endfor
    </ul>
</div>


<%def name="title()">Member List</%def>
