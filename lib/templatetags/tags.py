from django import template
import os
from django.conf import settings
from django.template import Context

register = template.Library()

LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 5
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 4
NUM_PAGES_OUTSIDE_RANGE = 1 
ADJACENT_PAGES = 2

@register.tag()
def digg_paginator(parser, token):
    try:
        tag_name, obj = token.split_contents()
    except ValueError:
        raise template.templateSyntaxError("%s tag requires one arguments" % token.contents.split()[0])
    return DiggPaginatorNode(obj)

class DiggPaginatorNode(template.Node):
    def __init__(self, obj):
        self.obj = template.Variable(obj)

    def render(self, context):
        request = context['request']
        obj = self.obj.resolve(context)
        data = {}
        queries_without_page = request.GET.copy()
        if queries_without_page.has_key('p'):
            del queries_without_page['p']

        data['queries'] = queries_without_page

        in_leading_range = in_trailing_range = False
        pages_outside_leading_range = pages_outside_trailing_range = range(0)
        pages = obj.paginator.num_pages 
        page = obj.number

        if (pages <= LEADING_PAGE_RANGE_DISPLAYED):
            in_leading_range = in_trailing_range = True
            page_numbers = [n for n in range(1, pages + 1) if n > 0 and n <= pages]           
        elif (page <= LEADING_PAGE_RANGE):
            in_leading_range = True
            page_numbers = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1) if n > 0 and n <= pages]
            pages_outside_leading_range = [n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif (page > pages - TRAILING_PAGE_RANGE):
            in_trailing_range = True
            page_numbers = [n for n in range(pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, pages + 1) if n > 0 and n <= pages]
            pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
        else: 
            page_numbers = [n for n in range(page - ADJACENT_PAGES, page + ADJACENT_PAGES + 1) if n > 0 and n <= pages]
            pages_outside_leading_range = [n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
            pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]

        #data["base_url"] = context["base_url"],
        #data["is_paginated"] = context["is_paginated"],

        try:
            data["previous"] = obj.previous_page_number()
        except:
            data["previous"] = 1
            
        data["has_previous"] = obj.has_previous()
        try:
            data["next"] =  obj.next_page_number()
        except:
            data["next"] = 0

        data["has_next"] = obj.has_next()
        data["results_per_page"] = obj.paginator.per_page
        data["page"] = page
        data["pages"] = pages
        data["page_numbers"] = page_numbers
        data["in_leading_range"] = in_leading_range 
        data["in_trailing_range"] = in_trailing_range 
        data["pages_outside_leading_range"] = pages_outside_leading_range 
        data["pages_outside_trailing_range"] = pages_outside_trailing_range

        t = template.loader.get_template('digg_paginator.html')
        return t.render(Context(data, autoescape=context.autoescape))
