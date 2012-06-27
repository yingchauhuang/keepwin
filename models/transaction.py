from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
import datetime
from askbot import const
from askbot.twmode import twmode as twmodeconst
from django.core.urlresolvers import reverse

# Add by YC: To implementation payment transaction
#class TransactionAuditStatus(models.Model):
#    """bridge "through" relation between activity and users"""
#    STATUS_NEW = 0
#    STATUS_SEEN = 1
#    STATUS_CHOICES = (
#        (STATUS_NEW, 'new'),
#        (STATUS_SEEN, 'seen')
#    )
#    user = models.ForeignKey(User)
#    transaction = models.ForeignKey('Transaction')
#    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_NEW)
#
#    class Meta:
#        unique_together = ('user', 'transaction')
#        app_label = 'askbot'
#        db_table = u'askbot_transactionauditstatus'
#
#    def is_new(self):
#        return (self.status == self.STATUS_NEW)
    
class TransactionManager(models.Manager):
    def get_question_transaction(self,user,question):
        if ((user is not None) and (question is not None)):
            return self.filter(user=user, question=question, transaction_type=twmodeconst.TYPE_TRANSACTION_PAID_FOR_CONTENT).count()
        else:
            return 0
#        return self.get_query_set().filter(user=user,question=question)

    def delete_paid_transaction(self,tid):
        #This function only handle the delete of TYPE_TRANSACTION_PAID_FOR_CONTENT transaction
        delete_trans =Transaction.objects.get(id=tid) 
        if (delete_trans.transaction_type==twmodeconst.TYPE_TRANSACTION_PAID_FOR_CONTENT):
            relate_trans=Transaction.objects.filter(refer=delete_trans)
            for relate_tran in relate_trans:
                relate_tran.delete_transaction()
            delete_trans.delete_transaction()
            
    def get_user_by_transactionID(self,tid):
        if ((tid is not None)):
            try:
                transaction=self.get(pk=tid)
                return transaction.user_id
            except:
                return None
        else:
            return None
        

class Transaction(models.Model):
    """
    We keep some history data for user transaction
    """
    user = models.ForeignKey(User)
    income = models.DecimalField(default=0,max_digits=6, decimal_places=2)
    outcome = models.DecimalField(default=0,max_digits=6, decimal_places=2)
    transaction_type = models.SmallIntegerField(choices = twmodeconst.TYPE_TRANSACTION)
    trans_at = models.DateTimeField(default=datetime.datetime.now)
    balance=models.DecimalField(default=0,max_digits=8, decimal_places=2)
    #todo: remove this denorm question field when Post model is set up
    question = models.ForeignKey('Post', null=True)
    refer = models.ForeignKey('Transaction', null=True)
    #amount = models.SmallIntegerField(default=0)
    #is_auditted = models.BooleanField(default=False)
    #add summary field.
    comment = models.CharField(max_length=128, null=True)

    objects = TransactionManager()


    def __unicode__(self):
        return u'[%s] add transaction at %s' % (self.user.username, self.trans_at)

    class Meta:
        app_label = 'askbot'
        db_table = u'transaction'

#    def add_recipients(self, recipients):
#        """have to use a special method, because django does not allow
#        auto-adding to M2M with "through" model
#        """
#        for recipient in recipients:
#            #todo: may optimize for bulk addition
#            aas = TransactionAuditStatus(user = recipient, activity = self)
#            aas.save()

    def delete_transaction(self):
        user = self.user

        new_balance = user.balance - self.income + self.outcome
        if new_balance < 0:
            new_balance = 0 #todo: magic number
            self.income = user.balance + self.outcome
        user.balance = new_balance
        user.save()
        self.delete()

    def get_explanation_snippet(self):
        """returns HTML snippet with a link to related question
        or a text description for a the reason of the reputation change

        in the implementation description is returned only 
        for Repute.reputation_type == 10 - "assigned by the moderator"

        part of the purpose of this method is to hide this idiosyncracy
        """
        if (self.transaction_type != twmodeconst.TYPE_TRANSACTION_PAID_FOR_CONTENT and self.transaction_type != twmodeconst.TYPE_TRANSACTION_RECEIVE_FROM_CONTENT):#todo: hide magic number
            if (self.transaction_type == twmodeconst.TYPE_TRANSACTION_BUY_IBON_ISSUE_CONFIRM):
                return  _('<em>ISSUE confirm. Reason:</em> %(reason)s') \
                                                    % {'reason':self.comment}
            elif (self.transaction_type == twmodeconst.TYPE_TRANSACTION_BUY_IBON_ISSUE):
                return _('<em>ISSUE iBon. Reason:</em> %(reason)s') \
                                                    % {'reason':self.comment} +unicode('<a href="https://ssl.smse.com.tw/ezpos/roturl.asp?Dcvc=2644&Rvg2c=1&Data_id=')+unicode(self.id)+_('" title="I want to re-check now">re-check</a>')                                    
            elif (self.transaction_type == twmodeconst.TYPE_TRANSACTION_BUY_IBON_ISSUE_ERROR):
                return  _('<em>ISSUE error. Reason:</em> %(reason)s') \
                                                    % {'reason':self.comment}
            else:
                return  _('<em>Bought the point. Reason:</em> %(reason)s') \
                                                    % {'reason':self.comment}
        else:
            delta = self.income - self.outcome
            link_title_data = {
                                'points': abs(delta),
                                'username': self.user.username,
                                'question_title': self.question.thread.title
                            }
            if delta > 0:
                link_title = _(
                                '%(points)s points were added for %(username)s\'s '
                                'contribution to question %(question_title)s'
                            ) % link_title_data
            else:
                link_title = _(
                                '%(points)s points were subtracted for %(username)s\'s '
                                'contribution to question %(question_title)s'
                            ) % link_title_data

            return '<a href="%(url)s" title="%(link_title)s">%(question_title)s</a>' \
                            % {
                               'url': self.question.get_absolute_url(), 
                               'question_title': self.question.thread.title,
                               'link_title': link_title
                            }

    def get_explanation_snippet_admin(self):
        """returns HTML snippet with a link to related question
        or a text description for a the reason of the reputation change

        in the implementation description is returned only 
        for Repute.reputation_type == 10 - "assigned by the moderator"

        part of the purpose of this method is to hide this idiosyncracy
        """
        if (self.transaction_type != twmodeconst.TYPE_TRANSACTION_PAID_FOR_CONTENT and self.transaction_type != twmodeconst.TYPE_TRANSACTION_RECEIVE_FROM_CONTENT):#todo: hide magic number
            if (self.transaction_type == twmodeconst.TYPE_TRANSACTION_BUY_IBON_ISSUE_CONFIRM):
                return  _('<em>ISSUE confirm. Reason:</em> %(reason)s') \
                                                    % {'reason':self.comment} +unicode('<a href="https://ssl.smse.com.tw/ezpos/roturl.asp?Dcvc=2644&Rvg2c=1&Data_id=')+unicode(self.id)+_('" title="I want to re-check now">re-check</a>')                                    
            elif (self.transaction_type == twmodeconst.TYPE_TRANSACTION_BUY_IBON_ISSUE):
                return _('<em>ISSUE iBon. Reason:</em> %(reason)s') \
                                                    % {'reason':self.comment} +unicode('<a href="https://ssl.smse.com.tw/ezpos/roturl.asp?Dcvc=2644&Rvg2c=1&Data_id=')+unicode(self.id)+_('" title="I want to re-check now">re-check</a>')                                    
            elif (self.transaction_type == twmodeconst.TYPE_TRANSACTION_BUY_IBON_ISSUE_ERROR):
                return  _('<em>ISSUE error. Reason:</em> %(reason)s') \
                                                    % {'reason':self.comment} +unicode('<a href="https://ssl.smse.com.tw/ezpos/roturl.asp?Dcvc=2644&Rvg2c=1&Data_id=')+unicode(self.id)+_('" title="I want to re-check now">re-check</a>')                                    
            else:
                return  _('<em>Bought the point. Reason:</em> %(reason)s') \
                                                    % {'reason':self.comment}
        else:
            delta = self.income - self.outcome
            link_title_data = {
                                'points': abs(delta),
                                'username': self.user.username,
                                'question_title': self.question.thread.title
                            }
            if delta > 0:
                link_title = _(
                                '%(points)s points were added for %(username)s\'s '
                                'contribution to question %(question_title)s'
                            ) % link_title_data
            else:
                link_title = _(
                                '%(points)s points were subtracted for %(username)s\'s '
                                'contribution to question %(question_title)s'
                            ) % link_title_data

            return '<a href="%(url)s" title="%(link_title)s">%(question_title)s</a>' \
                            % {
                               'url': self.question.get_absolute_url(), 
                               'question_title': self.question.thread.title,
                               'link_title': link_title
                            }

 