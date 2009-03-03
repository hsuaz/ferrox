import math

def populate_paging_links(pageno, num_pages, perpage, radius):
    links = []

    if not radius or pageno - radius <= 0:
        for n in xrange(0,pageno):
            links.append(('submit', n+1))
    else:
        links.append(('submit', 1))
        links.append(('...', '...'))
        for n in xrange(pageno-radius, pageno):
            links.append(('submit', n+1))

        
    links.append(('current', pageno+1))

    if not radius or pageno + radius >= num_pages:
        for n in xrange(pageno+1, num_pages):
            links.append(('submit', n+1))
    else:
        for n in xrange(pageno+1, pageno+radius):
            links.append(('submit', n+1))
        links.append(('...', '...'))
        links.append(('submit', num_pages))

    return links