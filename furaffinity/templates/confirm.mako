<%inherit file="base.mako" />

${h.form(c.url, method='post')}
% for k,v in c.fields.iteritems():
${h.hidden_field(k,value=v)}
% endfor
<div align="center">
${c.text}<br />
${h.submit('Yes', name='confirm')}
${h.submit('No', name='cancel')}
</div>
${h.end_form()}

<%def name="title()">Register</%def>

