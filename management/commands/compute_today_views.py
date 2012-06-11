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
        Post.objects.raw('UPDATE askbot_thread SET today_view_count=(select count(*) from askbot_post join askbot_questionview on askbot_post.id=askbot_questionview.question_id where TO_DAYS(askbot_questionview.when)=to_days(NOW()) and askbot_post.thread_id=askbot_thread.id);')
