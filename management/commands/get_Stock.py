"""Fetch the fund basic information
"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from askbot import models, forms
from django.utils.translation import ugettext as _
from askbot import models
import sys
from time import mktime 
import datetime
import lxml.html
from lxml import etree
import urllib


class Command(BaseCommand):
    "The command class itself"

    help = """
    """
    option_list = BaseCommand.option_list + (
        make_option('--URL',
            action = 'store',
            type = 'str',
            dest = 'URL',
            default = None,
            help = 'http link **required** !'
        ),
    )


    def handle(self, *args, **options):
        """fetch rss content and insert into forum with the username
        """

        if options['URL'] is None:
            raise CommandError('the --URL argument is required')
        
        URL = options['URL']
        try:
            ur = urllib.urlopen(URL)
            data = ur.read()
            data = unicode(data.decode('big5'))
            start=data.find('<table class="t04" border="0" cellspacing="0" cellpadding="0">')
            end=data.find('<img border="0" src="/funddj/images/Extend/BT_Info.gif" /></a></td></tr>')
            data=data[start:end]+'</a></td></tr></tbody></table>'
            tree = lxml.html.document_fromstring(data)
            items =tree.cssselect('tr td')
            '''
            tree = etree.parse(fileopen) 
            tree = etree.parse(data)
            items = doc.xpath('//table[@class="t04"]')[0]
            '''
            for item in items:
                print 'Item:' + item.text

        except:
            print "Unexpected error:", sys.exc_info()[0]