<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div class="basic-box FINISHME">
    <h2>${title()}
    % if c.page_owner == 'search' and c.search_terms['query_tags'] != None:
    (With tags: ${h.escape_once(c.search_terms['query_tags'])})
    % endif
    % if c.paging_links:
        ${c.form.start(h.implicit_url_for(tags=None, commit=None), method='post')}
        % if c.page_owner == 'search':
            ${c.form.hidden_field('query_main')}
            ${c.form.hidden_field('search_title')}
            ${c.form.hidden_field('search_description')}
            ${c.form.hidden_field('search_for')}
            ${c.form.hidden_field('query_author')}
            ${c.form.hidden_field('query_tags')}
        % else:
            ${c.form.hidden_field('tags')}
        % endif
        ${c.form.hidden_field('perpage')}
        % for link in c.paging_links:
            % if link[0] == '...':
                ${link[1]}
            % elif link[0] == 'submit':
                ${c.form.submit(value=link[1], name='page')}
            % else:
                ${c.form.submit(value=link[1], name='page', disabled_='disabled')}
            % endif
        % endfor
        ${c.form.end()}
    % endif
    </h2>
    % if c.page_owner != 'search':
    <h2>
        ${c.form.start(h.implicit_url_for(tags=None, commit=None), method='post')}
        Return ${c.form.text_field('perpage', size=5)} results per page.<br>
        Filter: ${c.form.text_field('tags')}${c.form.submit('Filter')}
        ${c.form.end()}
    </h2>
    % endif

    % if c.is_mine:
    <p class="admin"> ${h.link_to('Submit Art', h.url_for(controller='gallery', action='submit', username=c.auth_user.username))} </p>
    % endif

    ${lib.thumbnail_grid(c.submissions)}
</div>

<%def name="title()">
% if c.page_owner == None:
Browse Artwork
% elif c.page_owner == 'search':
Search Results for &quot;${h.escape_once(c.search_terms['query_main'])}&quot;
% else:
Browsing Gallery for ${c.page_owner.display_name}
% endif
</%def>
