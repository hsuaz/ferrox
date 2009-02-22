import pylons.config
from pylons.decorators.secure import *

from ferrox.lib import filestore, tagging
from ferrox.lib.base import *
from ferrox.lib.formgen import FormGenerator
import ferrox.lib.pagination as pagination

import formencode
import re

from sqlalchemy import or_, and_, not_

class SearchController(BaseController):
    @check_perm('search.do')
    def index(self):
        """Form for full-text search."""

        c.form = FormGenerator()
        c.form.defaults['perpage'] = int(pylons.config.get('gallery.default_perpage',12))
        return render('search/index.mako')

    @check_perm('search.do')
    def do(self):
        """Form handler for full-text search."""

        # ... yeah. Stubbed for now.

        validator = model.form.SearchForm()
        try:
            c.search_terms = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.form = FormGenerator(form_error=error)
            return render('search/index.mako')
        c.form = FormGenerator()
        c.form.defaults = c.search_terms

        abort(400);
