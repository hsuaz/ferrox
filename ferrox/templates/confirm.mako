<%inherit file="base.mako" />

${c.empty_form.start(c.url, method='post')}
% for k,v in c.fields.iteritems():
${c.empty_form.hidden_field(k,value=v)}
% endfor
<div align="center">
${c.text}<br />
${c.empty_form.submit('Yes', name='confirm')}
${c.empty_form.submit('No', name='cancel')}
</div>
${c.empty_form.end()}

<%def name="title()">Confirm</%def>

