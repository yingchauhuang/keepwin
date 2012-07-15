"""compute_today_views management command
to run type (on the command line:)

python manage.py compute_today_views
"""
from django.core.management.base import NoArgsCommand
from askbot.models.post import Post

class Command(NoArgsCommand):
    """Command class for "fix_newsQ" 
    """

    def handle(self, *arguments, **options):
        """function that handles the command job
        """
        Post.objects.raw('UPDATE auth_user SET receive_points=(select sum(income) from transaction where auth_user.id=transaction.user_id and transaction.transaction_type=20);')
