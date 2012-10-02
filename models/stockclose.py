from django.db import models
from django.utils.translation import ugettext as _
import datetime
import feedparser
import sys
import time
from time import mktime 
from askbot import const

class stockcloseManager(models.Manager):
    def Insert(self,Symbol,tDate,Open,High,Low,Close,Volume):
        CloseTick=stockclose.objects.get(Symbol=Symbol,tDate=tDate)
        if CloseTick==None:
            CloseTick=stockclose(Symbol=Symbol,tDate=tDate,Open=Open,High=High,Low=Low,Close=Close,Volume=Volume)
        else:
            CloseTick.Symbol=Symbol
            CloseTick.tDate=tDate
            CloseTick.Open=Open
            CloseTick.High=High            
            CloseTick.Low=Low
            CloseTick.Close=Close
            CloseTick.Volume=Volume
        CloseTick.save()
    def Get(self,Symbol,beginDate,endDate):
        return stockclose.objects.filter(Symbol=Symbol,tDate__gte=beginDate,tDate__lte=endDate)

        

class stockclose(models.Model):
    """
    The DB to store the Stock Close price
    """
    Symbol = models.CharField(max_length=8)
    tDate = models.DateField(default=datetime.date.today(),verbose_name=_('Trans_Date'))
    Open=models.FloatField(default=0,verbose_name=_('Open'))
    High=models.FloatField(default=0,verbose_name=_('High'))
    Low=models.FloatField(default=0,verbose_name=_('Low'))
    Close=models.FloatField(default=0,verbose_name=_('Close'))
    Volume=models.IntegerField(default=0,verbose_name=_('Volume'))
    objects = stockcloseManager()


    def __unicode__(self):
        return u'Symbol:%s' % (self.Symbol)

    class Meta:
        app_label = 'askbot'
        db_table = u'stockclose'
        verbose_name = _('stockclose')
        verbose_name_plural = _('stockclose')
    
class stocksymbolManager(models.Manager):
    def Insert(self,Symbol,Name,SName,CUR,Unit,Reference,EName,SEName):
        stocksymbol=stocksymbol.objects.get(Symbol=Symbol)
        if stocksymbol==None:
            stocksymbol=stocksymbol(Symbol=Symbol,Name=Name,SName=SName,CUR=CUR,Unit=Unit,Reference=Reference,EName=EName,SEName=SEName)
        else:
            stocksymbol.Symbol=Symbol
            stocksymbol.Name=Name
            stocksymbol.SName=SName
            stocksymbol.CUR=CUR
            stocksymbol.Unit=Unit
            stocksymbol.Reference=Reference
            stocksymbol.EName=EName
            stocksymbol.SEName=SEName
        CloseTick.save()
    def Get(self,Symbol):
        return stocksymbol.objects.filter(Symbol__contains=Symbol)

        

class stocksymbol(models.Model):
    """
    The DB to store the Stock Close proce
    """
    Symbol = models.CharField(max_length=8,primary_key=True)
    Market = models.CharField(max_length=8)
    Name = models.CharField(max_length=20,verbose_name=_('Stock Name'))
    SName = models.CharField(max_length=40,verbose_name=_('Short Name'))
    CUR = models.CharField(max_length=40,verbose_name=_('Currency'))
    Unit=models.IntegerField(default=0,verbose_name=_('Unit'))
    Reference=models.FloatField(default=0,verbose_name=_('Reference'))
    EName = models.CharField(max_length=20,verbose_name=_('Stock English Name'))
    SEName = models.CharField(max_length=40,verbose_name=_('Short English Name'))
    Uplimit=models.FloatField(default=0,verbose_name=_('Uplimit'))
    Downlimit=models.FloatField(default=0,verbose_name=_('Downlimit'))
    objects = stockcloseManager()


    def __unicode__(self):
        return u'Symbol:%s' % (self.Symbol)

    class Meta:
        app_label = 'askbot'
        db_table = u'stocksymbol'
        verbose_name = _('stocksymbol')
        verbose_name_plural = _('stocksymbol')
    



