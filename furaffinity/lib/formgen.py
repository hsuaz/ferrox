"""
Form tag helpers

Originally stolen and stripped down from the Pylons webhelpers module.
"""

import re
from webhelpers.rails.urls import confirm_javascript_function
from webhelpers.rails.tags import *
from webhelpers.util import html_escape

class FormGenerator(object):
    def __init__(self, error_class='form-error'):
        self.error_class = error_class
        self.errors = dict()
        self.defaults = dict()

    def get_error(self, name):
        if not name in self.errors:
            return ''

        return content_tag('span', self.errors[name], class_=self.error_class)

    def start(self, url, method="POST", multipart=False, **options):
        """
        Starts a form tag that points the action to an url. 
        
        The url options should be given either as a string, or as a ``url()``
        function. The method for the form defaults to POST.
        
        Options:

        ``multipart``
            If set to True, the enctype is set to "multipart/form-data".
        ``method``
            The method to use when submitting the form, usually either "GET" or 
            "POST". If "PUT", "DELETE", or another verb is used, a hidden input
            with name _method is added to simulate the verb over POST.
        
        """
        if multipart:
            options["enctype"] = "multipart/form-data"

        if callable(url):
            url = url()
        else:
            url = html_escape(url)

        options['method'] = method
        options["action"] = url
        return tag("form", True, **options)

    def end(self):
        """
        Outputs "</form>"
        """
        return "</form>"

    def select(self, name, option_tags='', **options):
        """
        Creates a dropdown selection box
        
        ``option_tags`` is a string containing the option tags for the select box::

            >>> select("people", "<option>George</option>")
            '<select id="people" name="people"><option>George</option></select>'
        
        Options:
        
        * ``multiple`` - If set to true the selection will allow multiple choices.
        
        """
        o = {'name_': name}
        o.update(options)
        return content_tag("select", option_tags, **o) + self.get_error(name)

    def text_field(self, name, value=None, **options):
        """
        Creates a standard text field.
        
        ``value`` is a string, the content of the text field
        
        Options:
        
        * ``disabled`` - If set to True, the user will not be able to use this input.
        * ``size`` - The number of visible characters that will fit in the input.
        * ``maxlength`` - The maximum number of characters that the browser will allow the user to enter.
        
        Remaining keyword options will be standard HTML options for the tag.
        """
        o = {'type': 'text', 'name_': name, 'value': value}
        o.update(options)

        if o['value'] == None and name in self.defaults:
            o['value'] = self.defaults[name]

        return tag("input", **o) + self.get_error(name)

    def hidden_field(self, name, value=None, **options):
        """
        Creates a hidden field.
        
        Takes the same options as text_field
        """
        return text_field(name, value, type="hidden", **options)

    def file_field(self, name, value=None, **options):
        """
        Creates a file upload field.
        
        If you are using file uploads then you will also need to set the multipart option for the form.

        Example:

            >>> file_field('myfile')
            '<input id="myfile" name="myfile" type="file" />'
        """
        return text_field(name, value=value, type="file", **options)

    def password_field(self, name="password", value=None, **options):
        """
        Creates a password field
        
        Takes the same options as text_field
        """
        return text_field(name, value, type="password", **options)

    def text_area(self, name, content=None, **options):
        """
        Creates a text input area.
        
        Options:
        
        * ``size`` - A string specifying the dimensions of the textarea.
        
        Example::
        
            >>> text_area("body", '', size="25x10")
            '<textarea cols="25" id="body" name="body" rows="10"></textarea>'
        """
        if 'size' in options:
            options["cols"], options["rows"] = options["size"].split("x")
            del options['size']
        o = {'name_': name}
        o.update(options)

        if content == None:
            if name in self.defaults:
                content = self.defaults[name]
            else:
                content = ''

        return content_tag("textarea", content, **o) + self.get_error(name)

    def check_box(self, name, value="1", checked=False, **options):
        """
        Creates a check box.
        """
        o = {'type': 'checkbox', 'name_': name, 'value': value}
        o.update(options)
        if checked:
            o["checked"] = "checked"
        return tag("input", **o) + self.get_error(name)

    def radio_button(self, name, value, checked=False, **options):
        """Creates a radio button.
        
        The id of the radio button will be set to the name + value with a _ in
        between to ensure its uniqueness.
        """
        pretty_tag_value = re.sub(r'\s', "_", '%s' % value)
        pretty_tag_value = re.sub(r'(?!-)\W', "", pretty_tag_value).lower()
        html_options = {'type': 'radio', 'name_': name, 'value': value}
        html_options.update(options)
        if checked:
            html_options["checked"] = "checked"
        return tag("input", **html_options) + self.get_error(name)

    def submit(self, value="Save changes", name='commit', confirm=None, disable_with=None, **options):
        """Creates a submit button with the text ``value`` as the caption.

        Options:

        * ``confirm`` - A confirm message displayed when the button is clicked.
        * ``disable_with`` - The value to be used to rename a disabled version of the submit
          button.
        """
        if confirm:
            onclick = options.get('onclick', '')
            if onclick.strip() and not onclick.rstrip().endswith(';'):
                onclick += ';'
            options['onclick'] = "%sreturn %s;" % (onclick, confirm_javascript_function(confirm))

        if disable_with:
            options["onclick"] = "this.disabled=true;this.value='%s';this.form.submit();%s" % (disable_with, options.get("onclick", ''))
        o = {'type': 'submit', 'name_': name, 'value': value }
        o.update(options)
        return tag("input", **o)

__all__ = ['FormGenerator']

