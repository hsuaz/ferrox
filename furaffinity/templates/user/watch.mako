<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako"/>

${lib.user_linkbar(c.user)}

<p> You have requested to watch the user ${c.user.display_name}. </p>
<p> ${c.form.start(h.url(controller='user', action='watch_confirm', username=c.user.username))}
What would you like to watch?
${c.form.check_box('submissions')} Submissions
${c.form.check_box('journals')} Journals
${c.form.submit("Watch %s"%c.user.display_name)}
${c.form.end()}
</p>

<%def name="title()">${c.user.display_name}</%def>
