"""management command that
creates the askbot user account programmatically
the command can add password, but it will not create
associations with any of the federated login providers
"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from askbot import models, forms
from django.utils.translation import ugettext as _
from askbot import models
import sys
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    "The command class itself"

    help = """
    """
    option_list = BaseCommand.option_list + (
        make_option('--model',
            action = 'store',
            type = 'str',
            dest = 'model',
            default = None,
            help = 'model Name is **required** ! Please use --model'
        ),
                                             
        make_option('--app_label',
            action = 'store',
            type = 'str',
            dest = 'app_label',
            default = None,
            help = 'app_label is **required** ! Please use --app_label'
        ),
    )


    def handle(self, *args, **options):
        """fetch rss content and insert into forum with the username
        """

        if options['model'] is None:
            raise CommandError('the --model argument is required')
        model = options['model']

        if options['app_label'] is None:
            raise CommandError('the --app_label argument is required')
        app_label = options['app_label']

        try:
            model=ContentType.objects.get(app_label=app_label, model=model)
            model.full_clean()

        except:
            print "Unexpected error:", sys.exc_info()[0]