from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
import datetime
from askbot.twmode import twmode as twmodeconst
from django.core.urlresolvers import reverse

class ProfileLayout(models.Model):
    """
    The block in each user layout
    """
    title = models.CharField(max_length=30)
    layout_type = models.SmallIntegerField(choices = twmodeconst.TYPE_TRANSACTION)
    html = models.TextField(blank=True)
    comment = models.CharField(max_length=40, null=True)
    sample = models.TextField(blank=True)

    def __unicode__(self):
        return u'title:[%s] ProfileLayout text %s' % (self.title, self.html)

    def is_system_layout(self):
        if (self.layout_type==twmodeconst.TYPE_LAYOUT_SYSTEM):
            return True
        else:
            return False
        
    class Meta:
        app_label = 'askbot'
        db_table = u'profilelayout'


class UserProfileLayoutManager(models.Manager):
    '''
        user_update_template UserProfileLayout ID is the key
        return True is success False is failure 
    '''
    def update_template(
                        self,
                        userprofilelayoutid,
                        content='',
                        title='',
                    ):
        try:
            userprofilelayout=UserProfileLayout.objects.get(id=userprofilelayoutid)
            userprofilelayout.content=content
            userprofilelayout.title=title
            userprofilelayout.save()
            return True
        except django_exceptions.ObjectDoesNotExist:
            return False            

       
class UserProfileLayout(models.Model):
    """
    The block in each user layout
    """
    user = models.ForeignKey(User)
    profilelayout = models.ForeignKey(ProfileLayout)
    title = models.CharField(max_length=40, null=True)
    content = models.TextField(null=True)
    
    objects = UserProfileLayoutManager()

    def __unicode__(self):
        return u'[%s] add UserProfileLayout text %s' % (self.user.username, self.content)

    class Meta:
        app_label = 'askbot'
        db_table = u'userprofilelayout'
#    