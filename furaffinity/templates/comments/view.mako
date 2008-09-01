<%namespace name="comments" file="/comments/lib.mako"/>
<%inherit file="base.mako"/>

<ul class="mini-linkbar">
    <li>${h.link_to("%s Back" % h.image_tag('/images/icons/go-up.png', ''), '/' + c.post_url)}</li>
</ul>

${comments.comment_tree(c.comments, c.post_url)}

<%def name="title()">View Comments</%def>
