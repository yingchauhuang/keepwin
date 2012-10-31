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
import csv

class Command(BaseCommand):
    "The command class itself"

    help = """
    """
    option_list = BaseCommand.option_list + (
        make_option('--Stock_Symbol',
            action = 'store',
            type = 'str',
            dest = 'Stock_Symbol',
            default = None,
            help = 'filename **required**, for the symbol '
        ),
        make_option('--Stock_Ind',
            action = 'store',
            type = 'str',
            dest = 'Stock_Ind',
            default = None,
            help = 'filename **required**, for the symbol industry ratio '
        ),
        make_option('--IndustryDimension',
            action = 'store',
            type = 'str',
            dest = 'IndustryDimension',
            default = None,
            help = 'filename **required**, for the IndustryDimension '
        ),
        make_option('--Stock_ConceptGroup',
            action = 'store',
            type = 'str',
            dest = 'Stock_ConceptGroup',
            default = None,
            help = 'filename **required**, for the Stock_ConceptGroup '
        ),
        make_option('--Stock_ConceptGroupRalation',
            action = 'store',
            type = 'str',
            dest = 'Stock_ConceptGroupRalation',
            default = None,
            help = 'filename **required**, for the Stock_ConceptGroupRalation'
        ),
        
    )

    def handle(self, *args, **options):
        """insert tag relation
        """
        """if options['Symbol'] is None:
            raise CommandError('the --Symbol argument is required')
        
        if options['Stock_Ind'] is None:
            raise CommandError('the --Stock_Ind argument is required')
        
        if options['IndustryDimension'] is None:
            raise CommandError('the --IndustryDimension argument is required')
        """
        try:
            Symbol_FileName = options['Stock_Symbol']
        except:
            Symbol_FileName = None
        
        try:
            Stock_Ind_FileName = options['Stock_Ind']
        except:
            Stock_Ind_FileName = None
        
        try:
            IndustryDimension_FileName = options['IndustryDimension']
        except:
            IndustryDimension_FileName = None
            
        try:
            ConceptGroup_FileName = options['Stock_ConceptGroup']
        except:
            ConceptGroup_FileName = None
            
        try:
            ConceptGroupRalation_FileName = options['Stock_ConceptGroupRalation']
        except:
            ConceptGroupRalation_FileName = None
            
        mapping = {u'AS':u'TW',u'AD':u'TW',u'SH':u'SH',u'SZ':u'SZ',u'HK':u'HK',u'US':u'US',u'JP':u'JP',u'KS':u'KR',u'SI':u'SG',u'AM':u''}
                   
        if IndustryDimension_FileName != None:
            with open(IndustryDimension_FileName, 'rb') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
           
                models.stockindustry.objects.all().delete()
                for tline in spamreader:
                    try:
                        ID = tline[0].decode('utf-8')
                        Name = tline[1].decode('utf-8')
                        CNName = tline[2].decode('utf-8')
                        dimen1 = tline[3].decode('utf-8')
                        dimen2 = tline[4].decode('utf-8')
                        dimen3 = tline[5].decode('utf-8')
                        dimen4 = tline[6].decode('utf-8')
                        dimen5 = tline[7].decode('utf-8')
                        dimen6 = tline[8].decode('utf-8')
                        industry = models.stockindustry.objects.create(ID=ID,Name=Name,CNName=CNName,dimen1=dimen1,dimen2=dimen2,dimen3=dimen3,dimen4=dimen4,dimen5=dimen5,dimen6=dimen6)
                    except Exception, e:
                        print '(IndustryDimension)ID:'+tline[0].decode('utf-8')+' reason:'+unicode(e)+unicode(sys.exc_info()[0])
            
        if Symbol_FileName != None:
            with open(Symbol_FileName, 'rb') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
           
                models.stocksymbol.objects.all().delete()
                for tline in spamreader:
                    try:
                        #tline=line.split(",")
                        Market = tline[1].decode('utf-8').strip()
                        Symbol = tline[0].decode('utf-8').strip()+"."+Market
                        Name = tline[2].decode('utf-8').strip()
                        SName = tline[3].decode('utf-8').strip()
                        CUR = tline[4].decode('utf-8').strip()
                        Unit = tline[5].decode('utf-8').strip()
                        Reference = tline[6].decode('utf-8').strip()
                        EName = tline[7].decode('utf-8').strip()
                        SEName = tline[8].decode('utf-8').strip()
                        Uplimit = tline[9].decode('utf-8').strip()
                        Downlimit = tline[10].decode('utf-8').strip()
                        #PRatio = tline[4].decode('utf-8')
                        indratio = models.stocksymbol.objects.create(Symbol=Symbol,Market=Market,Name=Name,SName=SName,CUR=CUR,Unit=Unit,Reference=Reference,EName=EName,SEName=SEName,Uplimit=Uplimit,Downlimit=Downlimit)
                    except Exception, e:
                        print '(Symbol)Symbol:'+tline[0].decode('utf-8')+' reason:'+unicode(e)+unicode(sys.exc_info()[0])
                
                   
        if Stock_Ind_FileName != None:
            with open(Stock_Ind_FileName, 'rb') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
           
                models.stockindustryratio.objects.all().delete()
                for tline in spamreader:
                    try:
                        Market = mapping[tline[0].decode('utf-8')[0:2]]
                        Symbol = tline[0].decode('utf-8')[2:8].strip()+"."+Market
                        if Market==None or Market=='':
                            continue
                        try:
                            stocksymbol=models.stocksymbol.objects.get(Symbol=Symbol,Market=Market)
                            if stocksymbol==None or stocksymbol=='':
                                continue
                        except Exception, e:
                            print '(Stock_Ind)Symbol:'+Symbol+' reason:'+unicode(e)+unicode(sys.exc_info()[0])
                            continue
                        try:
                            IndID = tline[2].decode('utf-8')
                            Industry= models.stockindustry.objects.get(ID=IndID)
                            if Industry==None or Industry=='':
                                continue
                        except Exception, e:
                            print '(Stock_Ind)IndID:'+IndID+' reason:'+unicode(e)+unicode(sys.exc_info()[0])
                            continue
                    
                        PRatio = tline[4].decode('utf-8')
                        indratio = models.stockindustryratio.objects.create(Symbol=stocksymbol,Industry=Industry,PRatio=PRatio)
                    except Exception, e:
                        print '(Stock_Ind)Symbol:'+Symbol+' reason:'+unicode(e)+unicode(sys.exc_info()[0])
                


        if ConceptGroup_FileName != None:
            with open(ConceptGroup_FileName, 'rb') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
           
                models.stockconceptgroup.objects.all().delete()
                for tline in spamreader:
                    try:
                        #tline=line.split(",")
                        Market = tline[2].decode('utf-8').strip()
                        GroupSymbol = tline[0].decode('utf-8').strip()+"."+Market
                        Name = tline[1].decode('utf-8').strip()
                        
                        indratio = models.stockconceptgroup.objects.create(GroupSymbol=GroupSymbol,Name=Name)
                    except Exception, e:
                        print '(ConceptGroup)GroupSymbol:'+tline[0].decode('utf-8')+' reason:'+unicode(e)+unicode(sys.exc_info()[0])
        
        if ConceptGroupRalation_FileName != None:
            with open(ConceptGroupRalation_FileName, 'rb') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
           
                models.stockconceptgrouprelation.objects.all().delete()
                for tline in spamreader:
                    try:
                        Market = mapping[tline[0].decode('utf-8')[0:2]]
                        StockSymbol = tline[0].decode('utf-8')[2:8].strip()+"."+Market
                        if Market==None or Market=='':
                            continue
                        GroupSymbol = tline[2].decode('utf-8').strip()+"."+Market
                        
                        try:
                            stock=models.stocksymbol.objects.get(Symbol=StockSymbol,Market=Market)
                            if stock==None or stock=='':
                                continue
                        except Exception, e:
                            print '(ConceptGroupRalation)StockSymbol:'+StockSymbol+' reason:'+unicode(e)+unicode(sys.exc_info()[0])
                            continue
                        try:
                            group= models.stockconceptgroup.objects.get(GroupSymbol=GroupSymbol)
                            if group==None or group=='':
                                continue
                        except Exception, e:
                            print '(ConceptGroupRalation)GroupSymbol:'+GroupSymbol+' reason:'+unicode(e)+unicode(sys.exc_info()[0])
                            continue

                        grouprelation = models.stockconceptgrouprelation.objects.create(stock=stock,group=group)
                    except Exception, e:
                        print '(ConceptGroupRalation)ConceptGroupRalation:'+tline[0].decode('utf-8')+tline[2].decode('utf-8')+' reason:'+unicode(e)+unicode(sys.exc_info()[0])
             
                
        stocks = models.stocksymbol.objects.all().all()
        for stock in stocks:
            Inds = models.stockindustryratio.objects.filter(Symbol=stock)
            tagName=""
            for Ind in Inds:
                if not (Ind.Industry.Name.strip() in tagName):
                    tagName= tagName + Ind.Industry.Name.strip() + ' '
            stock.tagnames=tagName
            stock.save()
