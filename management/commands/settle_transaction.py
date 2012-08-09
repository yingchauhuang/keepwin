"""fix_answer_counts management command
to run type (on the command line:)

python manage.py fix_answer_counts
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import signals
from askbot import models
from optparse import make_option

class Command(BaseCommand):
    """Command class for "fix_newsQ" 
    """
    help = """
    """
    option_list = BaseCommand.option_list + (
        make_option('--year',
            action = 'store',
            type = 'str',
            dest = 'year',
            default = None,
            help = 'year **required** !'
        ),
        make_option('--month',
            action = 'store',
            type = 'str',
            dest = 'month',
            default = None,
            help = 'month **required** !'
        ),
        make_option('--day',
            action = 'store',
            type = 'str',
            dest = 'day',
            default = None,
            help = 'day **required** !'
        ),
    )

    def handle(self, *arguments, **options):
        """function that handles the command job
        """
        if options['year'] is None:
            raise CommandError('the --year argument is required')
        if options['month'] is None:
            raise CommandError('the --month argument is required')
        if options['day'] is None:
            raise CommandError('the --day argument is required')
        
        year = int(options['year'])
        month = int(options['month'])
        day = int(options['day'])
        users = models.User.objects.all()
        for user in users:
            user.settle_transaction(year,month,day)
