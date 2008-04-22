<%namespace name="lib" file="/lib.mako"/>
<%inherit file="../base.mako" />

<div class="basic-box">
    % if c.page_owner == 'search':
    <h2>${title()}</h2>
    % else:
    <h2>Journal for ${lib.user_link(c.page_owner)}</h2>
    % endif
    % if c.is_mine:
    <p class="admin">${h.link_to('Post new journal', h.url(controller='journal', action='post', username=c.page_owner.username))}</p>
    % endif
    % if c.journal_page:
    % for entry in c.journal_page:
    ${lib.journal_entry(entry, True)}
    % endfor
    % else:
    <p> Journal is empty. </p>
    % endif
    </div>
    <p> ${c.journal_nav} </p>
</div>

<%def name="title()">
    % if c.page_owner == 'search':
    Search Results for &quot;${h.escape_once(c.search_terms['query_main'])}&quot;
    % else:
    Journal for ${c.page_owner.display_name}
    % endif
</%def>

