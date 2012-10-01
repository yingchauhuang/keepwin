"""Fetch the fund basic information
"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from askbot import models, forms
from django.utils.translation import ugettext as _
from askbot import models
import sys
from time import mktime 
import datetime



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
            help = 'file path **required** !'
        ),
        make_option('--update',
            action = 'store',
            type = 'int',
            dest = 'update',
            default = True,
            help = 'default value is True !'
        ),
    )


    def handle(self, *args, **options):
        """import stock daily price into database
        """

        if options['filename'] is None:
            raise CommandError('the --file argument is required')
        try:
            filename = options['filename']
            is_update= options['update']
            f = open(filename)
            for line in f:
                tline=line.split(",")
                tick_date = tline[0].encode('utf-8')
                tick_symbol = tline[1].encode('utf-8')
                tick_open = tline[2].encode('utf-8')
                tick_high = tline[3].encode('utf-8')
                tick_low = tline[4].encode('utf-8')
                tick_close = tline[5].encode('utf-8')
                tick_volume= tline[6].encode('utf-8')
                stockclosetick = models.stockclose.objects.get(tDate=tick_date,Symbol=tick_symbol)
                if (stockclosetick != None):
                    if (is_update):
                        stockclosetick.Open = tick_open
                        stockclosetick.High = tick_high
                        stockclosetick.Low = tick_low
                        stockclosetick.Close = tick_close
                        stockclosetick.Volume= tick_volume
                        stockclosetick.save()
                        print "Update:"+tick_symbol+" Date:"+ tick_date
                else:
                    stockclosetick = models.stockclose.objects.create(tDate=tick_date,Symbol=tick_symbol,Open=tick_open,High=tick_high,Low=tick_low,Close=tick_close,Volume=tick_volume)
                    stockclosetick.save()
                    print "Insert:"+tick_symbol+" Date:"+ tick_date
            f.close()
        except:
            print "Unexpected error:", sys.exc_info()[0]