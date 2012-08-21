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
        Post.objects.raw('UPDATE askbot_thread SET paid_count=(select count(*) from transaction left join askbot_post on askbot_post.id=transaction.question_id where transaction_type=10 and askbot_post.thread_id=askbot_thread.id);')
