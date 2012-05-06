"""management command that
creates the askbot user account programmatically
the command can add password, but it will not create
associations with any of the federated login providers
"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from askbot import models, forms

class Command(BaseCommand):
    "The command class itself"

    help = """
    """
    option_list = BaseCommand.option_list + (
        make_option('--filename',
            action = 'store',
            type = 'str',
            dest = 'filename',
            default = None,
            help = 'filename **required**, for the tagrelation '
        ),
        
    )

    def handle(self, *args, **options):
        """insert tag relation
        """
        if options['filename'] is None:
            raise CommandError('the --filename argument is required')

        filename = options['filename']

        f = open(filename, 'r')
        models.tag.TagRelation.objects.all().delete()
        for line in f:
            tline=line.split(",")
            symbol = tline[0].encode('utf-8')
            name = tline[1].encode('utf-8')
            Ind1 = tline[2].encode('utf-8')
            Ind2 = tline[3].encode('utf-8')
            if not tline[4] or tline[4]=='NULL':
                Percent =0
            else:
                Percent =tline[4]
            memo = tline[5].encode('utf-8')
            tagrelation = models.tag.TagRelation.objects.create(symbol,name,Ind1,Ind2,Percent,memo)

        f.close()

