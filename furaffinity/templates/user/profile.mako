<%inherit file="base.mako"/>

<dl>
% for datum in c.user.metadata:
    <dt>${datum.field.description}</dt>
    <dd>${datum.value}</dd>
% endfor
</dl>

<%def name="title()">${c.user.display_name}'s Profile</%def>
