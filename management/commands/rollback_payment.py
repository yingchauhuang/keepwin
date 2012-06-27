"""fix_answer_counts management command
to run type (on the command line:)

python manage.py fix_answer_counts
"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db.models import signals
from askbot import models
from askbot.models.transaction import Transaction

class Command(BaseCommand):
    """Command class for "rollback_payment" 
    """

    option_list = BaseCommand.option_list + (
        make_option('--TID',
            action = 'store',
            type = 'str',
            dest = 'TID',
            default = None,
            help = 'Transaction ID **required** !'
        ),
    )

    def handle(self, *arguments, **options):
        """function that handles the command job
        """
        if options['TID'] is None:
            raise CommandError('the --URL argument is required')
        
        TID = options['TID']
        Transaction.objects.delete_paid_transaction(TID)
