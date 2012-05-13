from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
import datetime
from django.core.urlresolvers import reverse

class ProfileLayoutManager(models.Manager):
        

class ProfileLayout(models.Model):
    """
    The block in each user layout
    """
    user = models.ForeignKey(User)
    title = models.CharField(max_length=30)
    layout_type = models.SmallIntegerField(choices = twmodeconst.TYPE_TRANSACTION)
    content = models.TextField(blank=True)

    objects = TransactionManager()


    def __unicode__(self):
        return u'[%s] add ProfileLayout text %s' % (self.user.username, self.content)

    class Meta:
        app_label = 'askbot'
        db_table = u'profilelayout'

#    