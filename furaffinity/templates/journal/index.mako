<%namespace name="lib" file="/lib.mako"/>
<%inherit file="../base.mako" />

<div class="basic-box">
    % if c.page_owner == 'search' or not c.page_owner:
    <h2>${title()}</h2>
    % else:
    <h2>Journal for ${lib.user_link(c.page_owner)}</h2>
    % endif
    % if c.paging_links:
        ${c.form.start(h.url(**c.page_link_dict), method='get')}
        % for link in c.paging_links:
            % if link[0] == 'current':
            ${c.form.submit(value=link[1], name='page', disabled_='disabled')}
            % elif link[0] == 'submit':
            ${c.form.submit(value=link[1], name='page')}
            % elif link[0] == '...':
            ${link[1]}
            % endif
        % endfor
        ${c.form.end()}
    % endif
    
    Year:
    % for x in xrange(2005,c.today.year+1):
        ${h.link_to(x, h.url(year=x, **c.by_date_base))}
    % endfor
    <br>
    
    % if c.month:
        Month: ${h.link_to('Last Month',h.url(**c.last_month))} 
        ${h.link_to('Next Month',h.url(**c.next_month))} <br>
    % elif c.year:
        Month:
        % for x in xrange(1,13):
            ${h.link_to(x, h.url(year=c.year, month=x, **c.by_date_base))}
        % endfor
        <br>
    % endif
    
    % if c.day:
    Day: ${h.link_to('Yesterday',h.url(**c.yesterday))} 
    ${h.link_to('Tomorrow',h.url(**c.tomorrow))} <br>
    % elif c.month:
        Day:
        % for x in xrange(1,c.days_this_month+1):
            ${h.link_to(x, h.url(year=c.year, month=c.month, day=x, **c.by_date_base))}
        % endfor
        <br>
    % endif
    
    % if c.is_mine:
    <p class="admin">${h.link_to('Post new journal', h.url(controller='journal', action='post', username=c.page_owner.username))}</p>
    % endif
    % if c.journals:
    % for entry in c.journals:
    % if c.title_only:
    ${h.link_to(entry.title, h.url(controller='journal', action='view', year=entry.time.year, month=entry.time.month, day=entry.time.month, id=entry.id, username=entry.user.username))}<br>
    % else:
    ${lib.journal_entry(entry, True)}
    % endif
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
    % elif not c.page_owner:
    Site-wide Journals
    % else:
    Journal for ${c.page_owner.display_name}
    % endif
</%def>

