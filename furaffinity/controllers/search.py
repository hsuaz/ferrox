from furaffinity.lib.base import *
from furaffinity.lib import filestore, tagging
from pylons.decorators.secure import *
from sqlalchemy import or_,and_,not_

import xapian
import re

class SearchController(BaseController):
    def index(self):
        return render('/search/index.mako')

        #return render('/PLACEHOLDER.mako')
    def do(self):
        validator = model.form.SearchForm();
        c.search_terms = None
        try:
            c.search_terms = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            return error

        query_parser = xapian.QueryParser()
        query_parser.set_default_op(xapian.Query.OP_AND)
        
        query_flags = xapian.QueryParser.FLAG_BOOLEAN|xapian.QueryParser.FLAG_LOVEHATE|xapian.QueryParser.FLAG_WILDCARD|xapian.QueryParser.FLAG_PURE_NOT;
        
        if c.search_terms['query_tags']:
            tag_query = query_parser.parse_query(c.search_terms['query_tags'],query_flags,'G')
        else:
            tag_query = None
            
        if c.search_terms['query_author']:
            author_object = model.retrieve_user(c.search_terms['query_author'].strip())
            author_query = query_parser.parse_query(str(author_object.id),query_flags,'A')
        else:
            author_query = None
        
        #These had better be here...
        title_query = query_parser.parse_query(c.search_terms['query_main'],query_flags,'T')
        post_query = query_parser.parse_query(c.search_terms['query_main'],query_flags,'P')

        if c.search_terms['search_title']:
            if c.search_terms['search_description']:
                main_query = xapian.Query(xapian.Query.OP_OR,title_query,post_query)
            else:
                main_query = title_query
        elif c.search_terms['search_description']:
            main_query = post_query
        else:
            abort(400)

        
        if tag_query != None:
            main_query = xapian.Query(xapian.Query.OP_AND,main_query,tag_query)
        if author_query != None:
            main_query = xapian.Query(xapian.Query.OP_AND,main_query,author_query)
            

        '''
        out = ''
        it = query.get_terms_begin()
        while it != query.get_terms_end():
            out = "%s '%s'"%(out,it.get_term())
            it.next()
        return out.strip()

        '''
        xapian_database = None
        if c.search_terms['search_for'] == 'submissions':
            xapian_database = xapian.Database('submission.xapian')
            table_class = model.Submission
        elif c.search_terms['search_for'] == 'journals':
            xapian_database = xapian.Database('journal.xapian')
            table_class = model.JournalEntry
        elif c.search_terms['search_for'] == 'news':
            xapian_database = xapian.Database('news.xapian')
            table_class = model.News
        else:
            abort(400)
            
        enquire = xapian.Enquire(xapian_database)
        enquire.set_query(main_query)
        results = enquire.get_mset(0,10)
        
        database_q = model.Session.query(table_class)
        
        limit = len(results)
        filter_eval = 'or_('
        for r in results:
            filter_eval = "%stable_class.c.id == %d, " % (filter_eval, int(r.document.get_value(0)[1:]))
        filter_eval += 'False)'
        database_q = database_q.filter(eval(filter_eval)).limit(limit)
        
        c.page_owner = 'search';
        if c.search_terms['search_for'] == 'submissions':
            c.submissions = database_q.all()
            return render('/gallery/index.mako')
        elif c.search_terms['search_for'] == 'journals':
            c.journal_page = database_q.all()
            return render('/journal/index.mako')
        elif c.search_terms['search_for'] == 'news':
            return render('/PLACEHOLDER.mako')
        
        return render(result_template)
        #return "<html>\n<body>\n<pre>%s</pre>\n</body>\n</html>\n"%str(database_q)
        
        