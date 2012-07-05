"""fix_answer_counts management command
to run type (on the command line:)

python manage.py fix_answer_counts
"""
from django.core.management.base import NoArgsCommand
from django.db.models import signals
from askbot import models

class Command(NoArgsCommand):
    """Command class for "fix_newsQ" 
    """
    def handle(self, *arguments, **options):
        """function that handles the command job
        """
        users = models.User.objects.all()
        for user in users:
            user.settle_transaction()
