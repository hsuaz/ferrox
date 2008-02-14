from furaffinity.lib.base import *
from furaffinity.lib import filestore, tagging
from pylons.decorators.secure import *

import xapian
import re

class SearchController(BaseController):
    def index(self):
        return render('/search/index.mako')

        #return render('/PLACEHOLDER.mako')
    def do(self):
        validator = model.form.SearchForm();
        submission_data = None
        try:
            submission_data = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            return error

        query_parser = xapian.QueryParser()
        query_parser.set_default_op(xapian.Query.OP_AND)
        
        query_flags = xapian.QueryParser.FLAG_BOOLEAN|xapian.QueryParser.FLAG_LOVEHATE|xapian.QueryParser.FLAG_WILDCARD|xapian.QueryParser.FLAG_PURE_NOT;
        
        if submission_data['query_tags']:
            tag_query = query_parser.parse_query(submission_data['query_tags'],query_flags,'G')
        else:
            tag_query = None
            
        if submission_data['query_author']:
            user_q = model.Session.query(model.User)
            try:
                author_object = user_q.filter_by(username = submission_data['query_author'].strip()).one()
            except sqlalchemy.exceptions.InvalidRequestError:
                c.error_text = "User %s not found." % h.escape_once(submission_data['query_author'])
                c.error_title = 'User not found'
                return render('/error.mako')
            
            author_query = query_parser.parse_query(str(author_object.id),query_flags,'A')
        else:
            author_query = None
        
        type_string = ''
        if submission_data['search_submissions']:
            type_string += 's '
        if submission_data['search_journals']:
            type_string += 'j '
        if submission_data['search_news']:
            type_string += 'n '
        if type_string == '':
            abort(400)
            
        query = query_parser.parse_query(type_string.strip(),xapian.QueryParser.FLAG_WILDCARD,'I')

        
        if tag_query != None:
            query = xapian.Query(xapian.Query.OP_AND,query,tag_query)
        if author_query != None:
            query = xapian.Query(xapian.Query.OP_AND,query,author_query)
            
        #These had better be here...
        title_query = query_parser.parse_query(submission_data['query_main'],query_flags,'T')
        post_query = query_parser.parse_query(submission_data['query_main'],query_flags,'P')

        if submission_data['search_title']:
            if submission_data['search_description']:
                main_query = xapian.Query(xapian.Query.OP_OR,title_query,post_query)
            else:
                main_query = title_query
        elif submission_data['search_description']:
            main_query = post_query
        else:
            abort(400)

        if query == None:
            query = main_query
        else:
            query = xapian.Query(xapian.Query.OP_AND,query,main_query)
        
        '''
        out = ''
        it = query.get_terms_begin()
        while it != query.get_terms_end():
            out = "%s '%s'"%(out,it.get_term())
            it.next()
        return out.strip()

        '''
        xapian_database = xapian.Database('fa.xapian')
        enquire = xapian.Enquire(xapian_database)
        enquire.set_query(query)
        results = enquire.get_mset(0,10)
        
        out = "<html>\n<body>\n<pre>\n"
        for r in results:
            out = "%s%s\n"%(out, r.document.get_value(0))
        
        return out+"</pre>\n</body>\n</html>\n"
        
