# encoding:utf-8
"""
:synopsis: views "Payemnt" 


"""

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotAllowed
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import Context
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils import translation
from django.views.decorators import csrf
from django.core.urlresolvers import reverse
from django.core import exceptions as django_exceptions
from django.conf import settings
from django.contrib.auth.models import User
from askbot.skins.loaders import render_into_skin, get_template
import askbot
import datetime
from askbot.models.rss import rss
import logging
#jinja2 template loading enviroment

# used in index page
#todo: - take these out of const or settings
from askbot.models import Post, Vote


def rss(request):
    """
    List of Questions, Tagged questions, and Unanswered questions.
    matching search query or user selection
    """

    user=request.user
    rsss=rss.objects.all()
    
    template_data = {
        'rsss': rsss,
        }

        #return render_into_skin('main_page_twmode.html', template_data, request)
    return render_into_skin('editor_rss.html', template_data, request)