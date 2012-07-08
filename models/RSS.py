from django.db import models
from django.utils.translation import ugettext as _
import datetime
import feedparser
import sys
import time
from time import mktime 
from askbot import const

class RSSManager(models.Manager):
    def set_tag(self,id,tag):
        if ((user is not None) and (question is not None)):
            return self.filter(user=user, question=question, transaction_type=twmodeconst.TYPE_TRANSACTION_PAID_FOR_CONTENT).count()
        else:
            return 0
#        return self.get_query_set().filter(user=user,question=question)


        

class RSS(models.Model):
    """
    The buffer to store the RSS
    """
    title = models.CharField(max_length=180)
    link = models.CharField(max_length=360)
    tagnames = models.CharField(default=None,max_length=125)
    guid = models.CharField(max_length=360,null=True,default=None)
    pubDate = models.DateTimeField(default=None,verbose_name=_('pubDate'))
    description = models.TextField(null=True)
    imported = models. NullBooleanField(default=False,verbose_name=_('imported'))
    objects = RSSManager()


    def __unicode__(self):
        return u'RSS:%s' % (self.title)

    class Meta:
        app_label = 'askbot'
        db_table = u'RSS'
        verbose_name = _('RSS')
        verbose_name_plural = _('RSS')
    
    def delete_RSS(self):
        self.delete()
        
    def import_RSS(self):
        self.delete()

class RSSSourceManager(models.Manager):
    def fetch(self):
        sources = RSSSource.objects.all()
        for source in sources:
            try:
                d=feedparser.parse(source.link)
            except feedparser.bozo_exception:
                d=feedparser.parse(source.link)
            try:
                print 'The RSS Channel title:' + d.feed.title
                print 'The RSS Channel description:' + d.feed.description
            except:
                print 'The RSS Channel Data ERROR !!!'
            
            try:
                for item in d.entries:
                    try:
                       # Make tuple to timestamp.
                       try:
                           ts = mktime(item.published_parsed)
                           dt = datetime.datetime.fromtimestamp(ts)
                       except:
                           try:
                               ts = mktime(time.strptime(item.published, '%a,%d %b %Y %H:%M:%S +0800'))
                               dt = datetime.datetime.fromtimestamp(ts)
                           except:
                               dt = datetime.datetime.now
                       # Transfer to datetime format.
                       
                       ntitle = item.title
                       nlink = item.links[0].href
                       nvalue = item.summary_detail.value
                       try:
                           guid = item.id
                       except:
                           guid = None
                       try:
                           if not RSS.objects.filter(link=nlink,pubDate=dt):
                                #print 'Insert Item:'+unicode(item.title.encode('utf8'),'utf8')
                                rss = RSS(
                                          title = ntitle,
                                          link = nlink,
                                          tagnames = None,
                                          guid = guid,
                                          pubDate = dt,
                                          description = nvalue,
                                          imported = False,
                                        )
                                rss.save()
                           else:
                                print 'Inserted already dropped Item:'+item.title
                       except askbot.models.post.DoesNotExist:
                                rss = RSS(
                                          title = ntitle,
                                          link = nlink,
                                          tagnames = None,
                                          guid = guid,
                                          pubDate = dt,
                                          description = nvalue,
                                          imported = False,
                                        )
                                rss.save()
                    except:
                        print "Unexpected error:", sys.exc_info()[0]
            except:
                    print "Unexpected error:", sys.exc_info()[0]
class RSSSource(models.Model):
    """
    The buffer to store the RSS
    """
    name = models.CharField(max_length=64)
    link = models.CharField(max_length=180)
    coding = models.CharField(max_length=16)
    fetchtime = models.DateTimeField(default=None,verbose_name=_('fetch Time'))
    numbers = models.PositiveIntegerField(default=0)
    success = models.PositiveIntegerField(default=0)
    objects = RSSSourceManager()


    def __unicode__(self):
        return u'RSSSource: %s' % (self.name, self.trans_at)

    class Meta:
        app_label = 'askbot'
        db_table = u'RSSSource'
        verbose_name = _('RSSSource')
        verbose_name_plural = _('RSSSource')
    
    def delete_transaction(self):
        self.delete()
        


