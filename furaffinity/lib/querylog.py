# Based very loosely on the code at
# http://www.sqlalchemy.org/trac/wiki/UsageRecipes/Profiling

from sqlalchemy.engine import Connection
from time import time
from thread import get_ident
from weakref import ref

thread_query_logs = {}

def _time(fn):
    start = time()
    fn()
    end = time()
    return end - start

# wrap _cursor_execute, _cursor_executemany w/ timing code
o1, o2 = Connection._cursor_execute, Connection._cursor_executemany
def _cursor_execute(self, c, statement, *args, **kwargs):
    t = _time(lambda: o1(self, c, statement, *args, **kwargs))
    query_log = thread_query_logs.get(get_ident(), None)
    if query_log:
        query_log().queries.append((statement, t))

def _cursor_executemany(self, c, statement, *args, **kwargs):
    t = _time(lambda: o2(self, c, statement, *args, **kwargs))
    query_log = thread_query_logs.get(get_ident(), None)
    if query_log:
        query_log().queries.append((statement, t))

Connection._cursor_execute = _cursor_execute
Connection._cursor_executemany = _cursor_executemany

class QueryLog(object):
    """Query logger for SQLAlchemy.

    Very simple at the moment.  Logging is done by thread, so be sure to
    create and release logger objects at the beginning and end of your
    requests.  I apologize for this kludge, but there doesn't seem to be any
    better way to hack into SQLAlchemy with the same precision.

    Queries are stored in self.queries as a list of (query, time) tuples.
    """
    def __init__(self):
        """Creates a new query logger and registers it to this thread."""
        self.queries = []
        thread_query_logs[get_ident()] = ref(self)

    def __del__(self):
        """Removes the logger for this thread."""
        try:
            del thread_query_logs[get_ident()]
        except KeyError:
            pass

    def time_elapsed(self):
        """Returns the total time spent in SQL since this logger was created.
        """
        total_time = 0
        for query, time in self.queries:
            total_time += time
        return total_time
