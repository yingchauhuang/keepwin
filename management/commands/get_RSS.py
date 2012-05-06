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
import feedparser
import sys
from time import mktime 
import datetime

class Command(BaseCommand):
    "The command class itself"

    help = """
    """
    option_list = BaseCommand.option_list + (
        make_option('--RSS',
            action = 'store',
            type = 'str',
            dest = 'RSS',
            default = None,
            help = 'RSS http link **required** !'
        ),
        make_option('--Coding',
            action = 'store',
            type = 'str',
            dest = 'coding',
            default = None,
            help = 'RSS content coding number **required** !'
        ),
        make_option('--user-name',
            action = 'store',
            type = 'str',
            dest = 'username',
            default = None,
            help = 'user name **required**, same as screen '
                    'name and django user name'
        ),
    )


    def handle(self, *args, **options):
        """fetch rss content and insert into forum with the username
        """

        if options['RSS'] is None:
            raise CommandError('the --RSS argument is required')
        if options['coding'] is None:
            raise CommandError('the --Coding argument is required')
        if options['username'] is None:
            raise CommandError('the --user-name argument is required')

        RSS = options['RSS']
        username = options['username']
        coding = options['coding']
        try:
            d=feedparser.parse(RSS)
        except feedparser.bozo_exception:
            d=feedparser.parse(RSS)
        print 'The RSS Channel title:' + d.feed.title
        print 'The RSS Channel description:' + d.feed.description
        try:
            users = models.User.objects.filter(username__icontains = username)
            user=users[0]
            for item in d.entries:
                try:
                   
                       # Make tuple to timestamp.
                    ts = mktime(item.published_parsed)
                    # Transfer to datetime format.
                    dt = datetime.datetime.fromtimestamp(ts)
                
    
                    ntitle = item.title
                    nlink = item.links[0].href
                    nvalue = item.summary_detail.value
                  
                    try:
                        if not models.Post.objects.filter(text=nvalue,added_at=dt):
                            #print 'Insert Item:'+unicode(item.title.encode('utf8'),'utf8')
                            question = user.post_question(
                                    title = ntitle,
                                    body_text = nvalue,
                                    tags = username,
                                    wiki = False,
                                    is_anonymous = False,
                                    timestamp = dt,
                                    is_charged = False,
                                    cost = 0,
                                    featurepic= None, 
                                )
                        else:
                            print 'Inserted already dropped Item:'+item.title
                    except askbot.models.post.DoesNotExist:
                         question = user.post_question(
                                    title = ntitle,
                                    body_text = nvalue,
                                    tags = username,
                                    wiki = False,
                                    is_anonymous = False,
                                    timestamp = dt,
                                    is_charged = False,
                                    cost = 0,
                                    featurepic= None, 
                                )
                except:
                    print "Unexpected error:", sys.exc_info()[0]
        except:
            print "Unexpected error:", sys.exc_info()[0]