"""fix_answer_counts management command
to run type (on the command line:)

python manage.py fix_answer_counts
"""
import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db.models import signals
from askbot import models
from askbot.models.transaction import Transaction
from askbot.conf import settings as askbot_settings
from decimal import *
from django.utils.translation import ugettext as _
from askbot import forms
import datetime
class Command(BaseCommand):
    """Command class for "rollback_payment" 
    """

    option_list = BaseCommand.option_list + (
        make_option('--Refer_id',
            action = 'store',
            type = 'str',
            dest = 'Refer_id',
            default = None,
            help = 'Reference ID **required** !'
        ),
        make_option('--Author_id',
            action = 'store',
            type = 'str',
            dest = 'Author_id',
            default = None,
            help = 'AUthor ID  !'
        ),
        make_option('--Admin_id',
            action = 'store',
            type = 'str',
            dest = 'Admin_id',
            default = None,
            help = 'Admin ID  !'
        ),
    )

    def handle(self, *arguments, **options):
        """function that handles the command job
        """
        if options['Refer_id'] is None:
            raise CommandError('the --Refer_id argument is required')
        
        if options['Author_id'] is not None:
            Author_id = options['Author_id']
        else:
            Author_id = None
                
        if options['Admin_id'] is not None:
            Admin_id = options['Admin_id']
        else:
            Admin_id = None
            
        Refer_id = options['Refer_id']
        
        transaction=Transaction.objects.get_transaction_by_ID(Refer_id)
        
        if transaction==None:
            raise CommandError('Can not find transaction by Refer_id')
        
        try:
            amount = transaction.outcome
            user = transaction.user
            qid = transaction.question.id
            per_author = Decimal(askbot_settings.PERCENT_FOR_AUTHOR)
            per_forum = Decimal(askbot_settings.PERCENT_FOR_FORUM)
            receive = Decimal(amount) * per_author/100
            toforum = Decimal(amount) * per_forum/100
            author = transaction.question.author
            if (Author_id is not None) and (Author_id != 'N'):
                
                comment = _('Receive')+unicode(receive)+_('Dollars')+_(' Puchase from:')+user.username
                user.add_user_transaction(
                                user = author,
                                income =receive,
                                outcome =0,
                                transaction_type=forms.TYPE_TRANSACTION_RECEIVE_FROM_CONTENT,
                                comment = comment,
                                timestamp = datetime.datetime.now(),
                                QID=qid,
                                refer=transaction 
                            )
            if (Admin_id is not None) and (Admin_id != 'N'):
                admin = models.User.objects.get(username = askbot_settings.NAME_OF_ADMINISTRATOR_USER)
                comment = _('Receive')+unicode(toforum)+_('Dollars')+_(' Puchase from:')+user.username+_(' Author:')+author.username
                user.add_user_transaction(
                                user = admin,
                                income =toforum,
                                outcome =0,
                                transaction_type=forms.TYPE_TRANSACTION_RECEIVE_FROM_CONTENT,
                                comment = comment,
                                timestamp = datetime.datetime.now(),
                                QID=qid,
                                refer=transaction
                            )
        except:
            message=unicode(sys.exc_info()[0])
            raise CommandError('Can not add transaction.. because:'+message)
'''
Created on 2013/6/6

@author: yhuang
'''
