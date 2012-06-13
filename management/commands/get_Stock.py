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
            data=data.replace('&nbsp;', ' ')
            tree = lxml.html.document_fromstring(data)
            items =tree.cssselect('tr td')
            '''
            tree = etree.parse(fileopen) 
            tree = etree.parse(data)
            items = doc.xpath('//table[@class="t04"]')[0]
            '''
            for item in items:
                if item.text!=None:
                    text= unicode(item.text)
                else:
                    text= unicode(item.text_content())

                if item.attrib['class']=='t2c1' or item.attrib['class']=='t2' :
                    title=text
                if item.attrib['class']=='t3t2':
                    content=text
                    print title + ' : '+content
        except:
            print "Unexpected error:", sys.exc_info()[0]