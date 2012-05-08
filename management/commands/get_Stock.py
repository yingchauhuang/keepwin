"""management command that
creates the askbot user account programmatically
the command can add password, but it will not create
associations with any of the federated login providers
"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from askbot import models, forms
from django.utils.translation import ugettext as _
from askbot import models
import sys
from time import mktime 
import datetime
from lxml import etree

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
        

        try:
            tree = etree.parse(URL)
            items = tree.xpath("//Item")
            for item in items:
                print 'The RSS Channel title:' + item.attrib['ID']
                print 'The RSS Channel description:' + item.attrib['Name']

        except:
            print "Unexpected error:", sys.exc_info()[0]