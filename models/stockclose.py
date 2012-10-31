from django.db import models
from django.utils.translation import ugettext as _
import datetime
import feedparser
import sys
import time
from time import mktime 
from askbot import const

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
    The DB to store the Stock Symbol
    """
    Symbol = models.CharField(max_length=11,primary_key=True)
    Market = models.CharField(max_length=8)
    Name = models.CharField(max_length=20,verbose_name=_('Stock Name'))
    SName = models.CharField(max_length=40,verbose_name=_('Short Name'))
    CUR = models.CharField(max_length=5,verbose_name=_('Currency'))
    Unit=models.IntegerField(default=0,verbose_name=_('Unit'))
    Reference=models.FloatField(default=0,verbose_name=_('Reference'))
    EName = models.CharField(max_length=50,verbose_name=_('Stock English Name'))
    SEName = models.CharField(max_length=80,verbose_name=_('Short English Name'))
    Uplimit=models.FloatField(default=0,verbose_name=_('Uplimit'))
    Downlimit=models.FloatField(default=0,verbose_name=_('Downlimit'))

    # Denormalised data, transplanted from Question
    tagnames = models.CharField(max_length=125)
    Parseing_Keys = models.CharField(max_length=125)
    objects = stocksymbolManager()


    def __unicode__(self):
        return u'Symbol:%s' % (self.Symbol)

    class Meta:
        app_label = 'askbot'
        db_table = u'stocksymbol'
        verbose_name = _('stocksymbol')
        verbose_name_plural = _('stocksymbol')
        
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
    Symbol = models.ForeignKey(stocksymbol, null=True, blank=True)
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
    
class stockindustry(models.Model):
    """
    The DB to store the Stock Close proce
    """
    ID = models.CharField(max_length=8,primary_key=True)
    Name = models.CharField(max_length=50,verbose_name=_('Industry Name'))
    CNName = models.CharField(max_length=50,verbose_name=_('Industry Chinese Name'))
    dimen1 = models.CharField(max_length=8,verbose_name=_('Dimension 1'))
    dimen2 = models.CharField(max_length=8,verbose_name=_('Dimension 2'))
    dimen3 = models.CharField(max_length=8,verbose_name=_('Dimension 3'))
    dimen4 = models.CharField(max_length=8,verbose_name=_('Dimension 4'))
    dimen5 = models.CharField(max_length=8,verbose_name=_('Dimension 5'))
    dimen6 = models.CharField(max_length=8,verbose_name=_('Dimension 6'))
    def __unicode__(self):
        return u'Industry Name:%s' % (self.Name)

    class Meta:
        app_label = 'askbot'
        db_table = u'stockindustry'
        verbose_name = _('stockindustry')
        verbose_name_plural = _('stockindustry')


class stockindustryratio(models.Model):
    """
    The DB to store the Stock Close price
    """
    Symbol = models.ForeignKey(stocksymbol, null=True, blank=True)
    #Market = models.CharField(max_length=8)
    Industry = models.ForeignKey(stockindustry, null=True, blank=True)
    PRatio = models.FloatField(default=0,verbose_name=_('Revenue Ration'))

    def __unicode__(self):
        return u'Symbol:%s' % (self.Symbol)

    class Meta:
        app_label = 'askbot'
        db_table = u'stockindustryratio'
        verbose_name = _('stockindustryratio')
        verbose_name_plural = _('stockindustryratio')


class stockconceptgroup(models.Model):
    """
    The DB to store the Stock Concept Group Relation
    """
    GroupSymbol = models.CharField(max_length=11,primary_key=True)
    Name = models.CharField(max_length=40,verbose_name=_('Group Name'))
    Parseing_Keys = models.CharField(max_length=125)

    def __unicode__(self):
        return u'GroupSymbol:%s' % (self.GroupSymbol)

    class Meta:
        app_label = 'askbot'
        db_table = u'stockconceptgroup'
        verbose_name = _('stockconceptgroup')
        verbose_name_plural = _('stockconceptgroup')

class stockconceptgrouprelation(models.Model):
    """
    The DB to store the Stock Concept Group Relation
    """
    group = models.ForeignKey(stockconceptgroup)
    stock = models.ForeignKey(stocksymbol)

    def __unicode__(self):
        return u'stockconceptgrouprelation:%s %s' % (self.group.Name,self.stock.Name)

    class Meta:
        app_label = 'askbot'
        db_table = u'stockconceptgrouprelation'
        verbose_name = _('stockconceptgrouprelation')
        verbose_name_plural = _('stockconceptgrouprelation')

