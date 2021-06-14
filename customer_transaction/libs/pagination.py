import os
from flask import abort
DEFAULT_PAGINATION_NUM_ELEMENTS = os.environ.get('DEFAULT_PAGINATION_NUM_ELEMENTS')


def get_paginated_list(results, url, start, limit):
    start = int(start)
    limit = int(limit) if limit != None else int(DEFAULT_PAGINATION_NUM_ELEMENTS)
    count = len(results)
    if count == 0:
        return {
            "count": 0,
            "results": []
        }
    if count < start or limit < 0:
        abort(404)
    # make response
    obj = {}
    obj['start'] = start
    obj['limit'] = limit
    obj['count'] = count
    # make URLs without query string
    url = request_url_without_query_string = url.split('?')[0]
    # make previous url
    if start == 1:
        obj['previous'] = ''
    else:
        start_copy = max(1, start - limit)
        # limit_copy = start - 1
        obj['previous'] = url + '?start=%d&limit=%d' % (start_copy, limit)
    # make next url
    if start + limit > count:
        obj['next'] = ''
    else:
        start_copy = start + limit
        obj['next'] = url + '?start=%d&limit=%d' % (start_copy, limit)
    # finally extract result according to bounds
    obj['results'] = results[(start - 1):(start - 1 + limit)]
    return obj