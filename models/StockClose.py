from django.db import models
from django.utils.translation import ugettext as _
import datetime
import feedparser
import sys
import time
from time import mktime 
from askbot import const

class StockCloseManager(models.Manager):
    def Insert(self,Symbol,tDate,Open,High,Low,Close,Volume):
        CloseTick=StockClose.objects.get(Symbol=Symbol,tDate=tDate)
        if CloseTick==None:
            CloseTick=StockClose(Symbol=Symbol,tDate=tDate,Open=Open,High=High,Low=Low,Close=Close,Volume=Volume)
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
        return StockClose.objects.filter(Symbol=Symbol,tDate__gte=beginDate,tDate__lte=endDate)

        

class StockClose(models.Model):
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
    objects = StockCloseManager()


    def __unicode__(self):
        return u'Symbol:%s' % (self.Symbol)

    class Meta:
        app_label = 'askbot'
        db_table = u'StockClose'
        verbose_name = _('StockClose')
        verbose_name_plural = _('StockClose')
    
class StockSymbolManager(models.Manager):
    def Insert(self,Symbol,Name,SName,CUR,Unit,Reference,EName,SEName):
        StockSymbol=StockSymbol.objects.get(Symbol=Symbol)
        if StockSymbol==None:
            StockSymbol=StockSymbol(Symbol=Symbol,Name=Name,SName=SName,CUR=CUR,Unit=Unit,Reference=Reference,EName=EName,SEName=SEName)
        else:
            StockSymbol.Symbol=Symbol
            StockSymbol.Name=Name
            StockSymbol.SName=SName
            StockSymbol.CUR=CUR
            StockSymbol.Unit=Unit
            StockSymbol.Reference=Reference
            StockSymbol.EName=EName
            StockSymbol.SEName=SEName
        CloseTick.save()
    def Get(self,Symbol):
        return StockSymbol.objects.filter(Symbol__contains=Symbol)

        

class StockSymbol(models.Model):
    """
    The DB to store the Stock Close proce
    """
    Symbol = models.CharField(max_length=8,primary_key=True)
    Name = models.CharField(max_length=20,verbose_name=_('Stock Name'))
    SName = models.CharField(max_length=40,verbose_name=_('Short Name'))
    CUR = models.CharField(max_length=40,verbose_name=_('Currency'))
    Unit=models.IntegerField(default=0,verbose_name=_('Unit'))
    Reference=models.FloatField(default=0,verbose_name=_('Reference'))
    EName = models.CharField(max_length=20,verbose_name=_('Stock English Name'))
    SEName = models.CharField(max_length=40,verbose_name=_('Short English Name'))
    Uplimit=models.FloatField(default=0,verbose_name=_('Uplimit'))
    Downlimit=models.FloatField(default=0,verbose_name=_('Downlimit'))
    objects = StockCloseManager()


    def __unicode__(self):
        return u'Symbol:%s' % (self.Symbol)

    class Meta:
        app_label = 'askbot'
        db_table = u'StockSymbol'
        verbose_name = _('StockSymbol')
        verbose_name_plural = _('StockSymbol')
    



