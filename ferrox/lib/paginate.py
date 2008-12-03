"""
Pagination for lists and ORMs

This module helps splitting up large lists of items into pages. The user gets
displayed one page at a time and can navigate to other pages. Imagine you are
offering a company phonebook and let the user search the entries. If the
search result contains 23 entries you may decide you display only 10 entries
per page. The first page contains entries 1-10, the second 11-20 and the third
21-23.

The Paginator itself maintains pagination logic associated with each page,
where it begins, what the first/last item on the page is, etc. The
navigator() method creates a link list allowing the user to switch to
other pages of the set.

This pagination module is an alternative to the paginator that comes with the
webhelpers module. It is in no way compatible so just replacing the import
statements will break your code. It uses the webhelpers.pagination.orm
module though.

This software can be used under the terms of the MIT license:

Copyright (c) 2007 Christoph Haas <email@christoph-haas.de>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# Use the ORM module from webhelper's pagination module
import webhelpers.pagination.orm as orm
import webhelpers
import nose
from pylons import c

__version__ = '$Revision: 100 $'
__author__ = 'Christoph Haas <email@christoph-haas.de>'

# Since the items on a page are mainly a list we subclass the "list" type
class Page(list):
    """
    Paginate a list/ORM of data

    The Paginator can be called on lists or with object-relational data.
    You will get a Paginator instance back that behaves basically like a
    list/iterable but has additional methods that are useful for paging
    through your data. If you iterate through this list you will just get
    the items back that are supposed to be displayed on the current page.

    If you want to page through data in a list you need to call the Paginator
    with a list as argument.

    If you want to page through data from a database you need to call the
    Paginator with either:

    - an SQLObject instance
    - an SQLAlchemy mapper instance (that you get from assign_mapper())
    - an SQLAlchemy query instance (model.session_context.current.query())
    - an SQLAlchemy table instance (that you define in models/)

    Current ORM support is limited to SQLObject and SQLAlchemy.

    **WARNING:** Unless you pass in an item_count, a count will be performed
    on the collection every time paginate is called. If using an ORM, it's
    suggested that you count the items yourself and/or cache them.
    """
    def __init__(self, collection, page_nr=0, items_per_page=20,
                item_count=None, *args, **options):
        """
        Parameters:

        collection: a list/tuple or SQLObject/SQLAlchemy object to page
        through

        page_nr: the number of the page to be displayed currently

        items_per_page: the maximal number of items to be displayed per page

        item_count: if you know the total number of items you should provide
        it because otherwise they are counted again by the paginator
        """
        # Decorate the ORM/sequence object with __getitem__ and __len__
        # functions to be able to get slices.
        if collection:
            self.collection = orm.get_wrapper(collection, *args, **options)
        else:
            self.collection = []

        try:
            self.page_nr = int(page_nr) # make it int() if we get it as a string
        except ValueError:
            self.page_nr = 0
        self.items_per_page = items_per_page

        # Unless the user tells us how many items the collections has
        # we calculate that ourselves.
        if item_count:
            self.item_count = item_count
        else:
            self.item_count = len(self.collection)

        # Compute the number of the first and last available page
        if self.item_count > 0:
            self.first_page = 0
            self.page_count = ((self.item_count - 1) / self.items_per_page) + 1
            self.last_page = self.first_page + self.page_count - 1
            import sys
            sys.stderr.write("{%d}" % self.item_count)

            # Make sure that the requested page number is valid
            if self.page_nr > self.last_page:
                self.page_nr = self.last_page
            elif self.page_nr < self.first_page:
                self.page_nr = self.first_page

            # Note: the number of items on this page can be less than
            #       items_per_page if the last page is not full
            self.first_item = self.page_nr * items_per_page
            self.last_item = min(self.first_item+items_per_page-1, self.item_count-1)

            # We subclassed "list" so we need to call its init() method
            # and fill the new list with the items to be displayed on the page
            self.items = self.collection[self.first_item:self.last_item+1]


        else:
            self.first_page = None
            self.page_count = 0
            self.last_page = None
            self.first_item = None
            self.last_item = None
            self.items = []

        list.__init__(self, self.items)


    def __repr__(self):
        return ("Paginator:\n"
            "Type:             %(type)s\n"
            "Page number:      %(page_nr)s\n"
            "First item:       %(first_item)s\n"
            "Last item:        %(last_item)s\n"
            "First page:       %(first_page)s\n"
            "Last page:        %(last_page)s\n"
            "Items per page:   %(items_per_page)s\n"
            "Number of items:  %(item_count)s\n"
            "Number of pages:  %(page_count)s\n"
            % {
            'type':type(self.collection),
            'page_nr':self.page_nr,
            'first_item':self.first_item,
            'last_item':self.last_item,
            'first_page':self.first_page,
            'last_page':self.last_page,
            'items_per_page':self.items_per_page,
            'item_count':self.item_count,
            'page_count':self.page_count,
            })

    def navigator(self, link_var='page_nr', radius=1,
        start_with_one=True, seperator=' ', show_if_single_page=False,
        ajax_id=None, framework='scriptaculous', **kwargs):
        """
        Returns a list of links to other page before and after the current
        page. Example: "1 2 [3] 4 5 6 7 8 >".

        link_var:
            The name of the parameter that will carry the number of the page the
            user just clicked on. The parameter will be passed to a url_for()
            call so if you stay with the default ':controller/:action/:id'
            routing and set link_var='id' then the :id part of the URL will be
            changed. If you set link_var='page_nr' then url_for() will make it
            an extra parameters like ':controller/:action/:id?page_nr=1'. You
            need the link_var in your action to determine the page number the
            user wants to see. If you do not specify anything else the default
            will be a parameter called 'page_nr'.

        radius:
            The number of pages left and right to the current page shown in the
            navigator. Examples::

                mypaginator.navigator(radius=1)    # the default
                1 .. 7 [8] 9 .. 500

                mypaginator.navigator(radius=3)
                1 .. 5 6 7 [8] 9 10 11 .. 500

                mypaginator.navigator(radius=5)
                1 .. 3 4 5 6 7 [8] 9 10 11 12 13 .. 500

        start_with_one:
            page numbers start with 0. If this flag is True then the user will
            see page numbers start with 1.

        seperator:
            the string used to seperate the page links (default: ' ')

        show_if_single_page:
            if True the navigator will be shown even if there is only one page
            (default: False)

        ajax_id:
            an optional string with the name of a HTML element (e.g. a <div
            id="foobar">) containing the paginated entries and the navigator
            itself. The navigator will create AJAX links (using webhelpers'
            link_to_remote() function) that replace the HTML element's content
            with the new page of paginated items and a new navigator.

        framework
            The name of the JavaScript framework to use. By default
            the AJAX functions from script.aculo.us are used. Supported
            frameworks:
            - scriptaculous
            - jquery

        Additional keyword arguments are used as arguments in the links.
        Otherwise the link will be created with url_for() which points to
        the page you are currently displaying.
        """

        def _link(pagenr, text):
            """
            Create a URL that links to another page
            """
            # Let the url_for() from webhelpers create a new link and set
            # the variable called 'link_var'. Example:
            # You are in '/foo/bar' (controller='foo', action='bar')
            # and you want to add a parameter 'pagenr'. Then you
            # call the navigator method with link_var='pagenr' and
            # the url_for() call will create a link '/foo/bar?pagenr=...'
            # with the respective page number added.
            # Further kwargs that are passed to the navigator will
            # also be added as URL parameters.
            arg_dict = {}
            if pagenr != self.first_page:
                arg_dict[link_var] = pagenr
            arg_dict.update(c.route)
            arg_dict.update(kwargs)
            link_url = webhelpers.url_for(**arg_dict)
            if ajax_id:
                # Return an AJAX link that will update the HTML element
                # named by ajax_id.
                if framework == 'scriptaculous':
                    return webhelpers.link_to_remote(text, dict(update=ajax_id,
                        url=link_url))
                elif framework == 'jquery':
                    return webhelpers.link_to(text,
                        onclick="""$('#%s').load('%s'); return false""" % \
                        (ajax_id, link_url))
                else:
                    raise exception, "Unsupported Javascript framework: %s" % \
                            framework

            else:
                # Return a normal a-href link that will call the same
                # controller/action with the link_var set to the new
                # page number.
                return webhelpers.link_to(text, link_url)

        # Don't show navigator if there is no more than one page
        if self.page_count <= 1 and show_if_single_page == False:
            return ''

        # Compute the number of pages before/after the current page
        leftmost_page = max(self.first_page, (self.page_nr-radius))
        rightmost_page = min(self.last_page, (self.page_nr+radius))

        nav_items = []

        # Create a link to the very first page (unless we are there already)
        if self.page_nr != self.first_page and leftmost_page>self.first_page:
            text = '%s' % (self.first_page+(start_with_one and 1))
            nav_items.append(_link(self.first_page, text))

        # Insert dots if there are pages between the first page
        # and the currently displayed page range
        if self.first_page < leftmost_page-1:
            nav_items.append('..')

        for thispage in xrange(leftmost_page, rightmost_page+1):
            # Hilight the current page number without a link
            if thispage == self.page_nr:
                text = '[<strong>%s</strong>]' % (thispage+(start_with_one and 1))
                nav_items.append(text)
            # Otherwise create just a link to that page
            else:
                text = '%s' % (thispage+(start_with_one and 1))
                nav_items.append(_link(thispage, text))

        # Insert dots if there are pages between the displayed
        # page numbers and the end of the page range
        if self.last_page > rightmost_page+1:
            nav_items.append('..')

        # Create a link to the very last page (unless we are there already)
        if self.page_nr != self.last_page and rightmost_page<self.last_page:
            text = '%s' % (self.last_page+(start_with_one and 1))
            nav_items.append(_link(self.last_page, text))
        return seperator.join(nav_items)

# Unit tests (useing Nose 0.9.3)
def testEmptyList():
    """
    Tests whether an empty list is handled correctly.
    """
    items = []
    paginator = Page(items, page_nr=0)
    assert paginator.page_nr==0
    assert paginator.first_item is None
    assert paginator.last_item is None
    assert paginator.first_page is None
    assert paginator.last_page is None
    assert paginator.items_per_page==20
    assert paginator.item_count==0
    assert paginator.page_count==0

def testOnePage():
    """
    Tries to fit 10 items on a 10-item page
    """
    items = range(10)
    paginator = Page(items, page_nr=0, items_per_page=10)
    assert paginator.page_nr==0
    assert paginator.first_item==0
    assert paginator.last_item==9
    assert paginator.first_page==0
    assert paginator.last_page==0
    assert paginator.items_per_page==10
    assert paginator.item_count==10
    assert paginator.page_count==1

def testTwoPages():
    """
    Tries to fit 11 items on two 10-item pages
    """
    items = range(11)
    paginator = Page(items, page_nr=0, items_per_page=10)
    assert paginator.page_nr==0
    assert paginator.first_item==0
    assert paginator.last_item==9
    assert paginator.first_page==0
    assert paginator.last_page==1
    assert paginator.items_per_page==10
    assert paginator.item_count==11
    assert paginator.page_count==2

# vim:tw=100:

