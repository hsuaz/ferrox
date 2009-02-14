"""
Form tag helpers

Originally stolen and stripped down from the Pylons webhelpers module.
"""

import formencode
import re
#from webhelpers.rails.urls import confirm_javascript_function
#from webhelpers.rails.tags import *
from webhelpers.html import *
from webhelpers.util import html_escape

def content_tag(tag, c, *args, **kwargs):
    return HTML.tag(tag, c=c, *args, **kwargs)
    
def tag(tag, *args, **kwargs):
    return HTML.tag(tag, *args, **kwargs)

# TODO: groups, i.e. checkboxen, radio buttons, and selects
# TODO: defaults for radio buttons and selects

class FormGenerator(object):
    def __init__(self, error_class='form-error', form_error=None):
        self.error_class = error_class
        if form_error:
            if form_error.value and not form_error.error_dict:
                # Something actually went wrong beyond form validation
                raise form_error
            self.errors = form_error.error_dict
            self.defaults = form_error.value
        else:
            self.errors = dict()
            self.defaults = dict()

    def error(self, text):
        return content_tag('span', text, class_=self.error_class)

    def get_error(self, name):
        if not name in self.errors:
            return ''

        return self.error(self.errors[name])

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

        if callable(url):
            url = url()
        else:
            url = html_escape(url)

        return tags.form(url, method, multipart, **options)

    def end(self):
        """
        Outputs "</form>"
        """
        return "</form>"

    def select(self, name, option_tags='', show_errors=True, **options):
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

        ret = content_tag("select", option_tags, **o)
        if show_errors:
            ret += self.get_error(name)
        return ret

    def text_field(self, name, value=None, show_errors=True, **options):
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

        ret = tag("input", **o)
        if show_errors:
            ret += self.get_error(name)
        return ret

    def hidden_field(self, name, value=None, **options):
        """
        Creates a hidden field.

        Takes the same options as text_field
        """
        return self.text_field(name, value, type="hidden", **options)

    def file_field(self, name, value=None, **options):
        """
        Creates a file upload field.

        If you are using file uploads then you will also need to set the multipart option for the form.

        Example:

            >>> file_field('myfile')
            '<input id="myfile" name="myfile" type="file" />'
        """
        return self.text_field(name, value=value, type="file", **options)

    def password_field(self, name="password", value=None, **options):
        """
        Creates a password field

        Takes the same options as text_field
        """
        return self.text_field(name, value, type="password", **options)

    def text_area(self, name, content=None, show_errors=True, **options):
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

        ret = content_tag("textarea", content, **o)
        if show_errors:
            ret += self.get_error(name)
        return ret

    def check_box(self, name, value='1', checked=None, label='',
                  show_errors=True, **options):
        """
        Creates a check box.
        """
        o = {'type': 'checkbox', 'name_': name, 'value': value}
        o.update(options)

        if checked == None and name in self.defaults:
            checked = self.defaults[name]
        if checked:
            o['checked'] = 'checked'

        ret = tag("input", **o)
        if label:
            ret += ' ' + label
        if show_errors:
            ret += self.get_error(name)
        return ret

    def radio_button(self, name, value, checked=False, show_errors=True, **options):
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

        ret = tag("input", **html_options)
        if show_errors:
            self.get_error(name)
        return ret

    def submit(self, value="Save changes", name=None, confirm=None, disable_with=None, **options):
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
            #options['onclick'] = "%sreturn %s;" % (onclick, confirm_javascript_function(confirm))
            options['onclick'] = onclick

        if name:
            options['name_'] = name

        if disable_with:
            options["onclick"] = "this.disabled=true;this.value='%s';this.form.submit();%s" % (disable_with, options.get("onclick", ''))

        o = {'type': 'submit'}
        o.update(options)
        #return content_tag('button', value, **o)
        return HTML.input(value=value, **o)
        
        

__all__ = ['FormGenerator']

