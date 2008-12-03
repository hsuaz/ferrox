<%inherit file="../base.mako" />

${next.body()}

<%def name="title()">${next.title()} - ${c.page_owner.display_name}'s Notes</%def>

