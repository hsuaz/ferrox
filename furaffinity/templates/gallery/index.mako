<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<div class="basic-box FINISHME">
    <h2>${title()}
    % if c.page_owner == 'search' and c.search_terms['query_tags'] != None:
    (With tags: ${h.escape_once(c.search_terms['query_tags'])})
    % endif
    </h2>
    % if c.page_owner != 'search':
    <h2>
        ${c.form.start(h.url(tags=None, commit=None), method='get')}
        Filter: ${c.form.text_field('tags')}${c.form.submit('Filter')}
        ${c.form.end()}
    </h2>
    % endif

    % if c.is_mine:
    <p class="admin"> ${h.link_to('Submit Art', h.url(controller='gallery', action='submit', username=c.auth_user.username))} </p>
    % endif
    % if c.submissions:
        % for item in c.submissions:
        <div class="submission">
            <div class="submission_header">
                <div class="submission_title">${h.link_to(item.title, h.url(controller='gallery', action='view', id=item.id, username=item.primary_artist().username))}</div>
                <div class="submission_date">Date: ${h.format_time(item.time)}</div>
            </div>
            <div class="submission_info">
                ${item.description_parsed}<br>
                % if item.get_derived_index(['thumb']) != None:
                <div class="submission_thumbnail">${h.image_tag(h.url_for(controller='gallery', action='file', filename=item.get_derived_by_type('thumb').metadata.get_filename()), item.title)}</div>
                % endif
            </div>
        </div>
        % endfor
    % else:
    <p> There are no submissions. </p>
    % endif
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
