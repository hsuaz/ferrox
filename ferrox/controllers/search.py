import pylons.config
from pylons.decorators.secure import *

from ferrox.lib import filestore, tagging
from ferrox.lib.base import *
from ferrox.lib.formgen import FormGenerator
import ferrox.lib.pagination as pagination

import formencode
import re

import xapian
from sqlalchemy import or_, and_, not_

if xapian.major_version() < 1:
    raise ImportError("xapian needs >=1.0 found %s" % xapian.version_string())

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

        validator = model.form.SearchForm()
        try:
            c.search_terms = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.form = FormGenerator(form_error=error)
            return render('search/index.mako')
        c.form = FormGenerator()
        c.form.defaults = c.search_terms

        query_parser = xapian.QueryParser()
        query_parser.set_default_op(xapian.Query.OP_AND)

        query_flags = xapian.QueryParser.FLAG_BOOLEAN \
                    | xapian.QueryParser.FLAG_LOVEHATE \
                    | xapian.QueryParser.FLAG_WILDCARD \
                    | xapian.QueryParser.FLAG_PURE_NOT

        tag_query = None
        if c.search_terms['query_tags']:
            tag_query = query_parser.parse_query(c.search_terms['query_tags'],
                                                 query_flags, 'G')

        author_query = None
        if c.search_terms['query_author'] and c.search_terms['query_author'] != 'None':
            author_object = model.User.get_by_name(
                c.search_terms['query_author'].strip())
            author_query = query_parser.parse_query(str(author_object.id),
                                                    query_flags, 'A')

        # These had better be here...
        title_query = query_parser.parse_query(c.search_terms['query_main'],
                                               query_flags, 'T')
        post_query = query_parser.parse_query(c.search_terms['query_main'],
                                              query_flags, 'P')

        if c.search_terms['search_title']:
            if c.search_terms['search_description']:
                main_query = xapian.Query(xapian.Query.OP_OR, title_query,
                                          post_query)
            else:
                main_query = title_query
        elif c.search_terms['search_description']:
            main_query = post_query
        else:
            abort(400)

        if tag_query != None:
            main_query = xapian.Query(xapian.Query.OP_AND, main_query,
                                      tag_query)
        if author_query != None:
            main_query = xapian.Query(xapian.Query.OP_AND, main_query,
                                      author_query)

        if c.search_terms['search_for'] == 'submissions':
            xapian_database = xapian.Database('submission.xapian')
            table_class = model.Submission
        elif c.search_terms['search_for'] == 'journals':
            xapian_database = xapian.Database('journal.xapian')
            table_class = model.JournalEntry
        else:
            abort(400)

        pageno = (c.search_terms['page'] if c.search_terms['page'] else 1)-1
        perpage = c.search_terms['perpage'] if c.search_terms['perpage'] else int(pylons.config.get('gallery.default_perpage',12))
        
        enquire = xapian.Enquire(xapian_database)
        enquire.set_query(main_query)
        results = enquire.get_mset(pageno*perpage, perpage, 10)
        if pylons.config.has_key('paging.radius'):
            paging_radius = int(pylons.config['paging.radius'])
        else:
            paging_radius = 3
            
        c.paging_links = pagination.populate_paging_links(pageno=pageno, num_pages=results.get_matches_estimated(), perpage=perpage, radius=paging_radius)
        database_q = model.Session.query(table_class)

        limit = len(results)
        if limit > 0:
            ids = []
            for r in results:
                ids.append(table_class.c.id == r.document.get_value(0)[1:])
            database_q = database_q.filter(or_(*ids))
        database_q = database_q.limit(limit)

        c.page_owner = 'search'
        if c.search_terms['search_for'] == 'submissions':
            c.submissions = database_q.all() if limit else []
            return render('/gallery/index.mako')
        elif c.search_terms['search_for'] == 'journals':
            c.journal_page = database_q.all() if limit else []
            return render('/journal/index.mako')

        abort(400);
