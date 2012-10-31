# -*- coding:big5
"""management command that
creates the askbot user account programmatically
the command can add password, but it will not create
associations with any of the federated login providers

Input file have change to UTF-8

"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from askbot import models, forms
import sys
from datetime import datetime

class Command(BaseCommand):
    "The command class itself"

    help = """
    """
    option_list = BaseCommand.option_list + (
        make_option('--file',
            action = 'store',
            type = 'str',
            dest = 'file',
            default = None,
            help = 'filename **required**, for parsing '
        ),
        
    )

    def handle(self, *args, **options):
        """insert tag relation
        """
        if options['file'] is None:
            raise CommandError('the --file argument is required')

        try:
            filename = options['file']
        except:
            filename = None
        
        f = open(filename)
        article_Title=""
        article_SubTitle=""
        article_Prolog=""
        for line in f:
            tline=line.decode('big5').split(",")
            if tline[3]== unicode("副標"):
                article_SubTitle=tline[4]
            elif tline[3]== unicode("前言"):
                article_Prolog=article_Title
            elif tline[3]== unicode("大標"):
                article_Period  = int(tline[0].encode('utf-8'))
                article_MainCategory = unicode(tline[1])
                article_SubCategory = unicode(tline[2])
                article_Title = unicode(tline[4])
                article_Content = unicode(tline[5])
                article_Author= unicode(tline[6])
                article_Tag = unicode(tline[7])
                article_Time = datetime.strptime(unicode(tline[8])[0:8],"%Y/%m/%d")
                article_Comment= unicode(tline[9])
                article_Path= unicode(tline[10])
                article_Image= unicode(tline[11])  
            if article_Title!="" and article_SubTitle!="" and article_Prolog!="" :
                #writer.add_document(Period=article_Period,\
                #        MainCategory=article_MainCategory,SubCategory=article_SubCategory,\
                #        Title=article_Title,SubTitle=article_SubTitle,Prolog=article_Prolog, Content=article_Content,\
                #        Author=article_Author,Tag=article_Tag,Time=article_Time,Path=article_Path,Image=article_Image)
                tagnames= list()  
                stocks=models.stocksymbol.objects.all()
                for stock in stocks:
                    parsing_keys=list()
                    parsing_keys.append(stock.Name)
                    parsing_keys.append(stock.SName)
                    for parsing_key in parsing_keys:
                        if len(parsing_key) > 0:
                            if ((parsing_key in article_Content) or (parsing_key in article_Title) or (parsing_key in article_Comment)):
                                if not (stock in tagnames):
                                    tagnames.append(stock)                   
                print article_Title+":"
                if len(tagnames) > 0 :
                    for stock in tagnames:
                        print '----'+stock.Name +'(出現次數:'+unicode(article_Content.count(unicode(stock.Name)))+') '+stock.tagnames
                article_Title=""
                article_SubTitle=""
                article_Prolog=""
        f.close()           
        