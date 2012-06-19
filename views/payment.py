# encoding:utf-8
"""
:synopsis: views "Payemnt" 


"""

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotAllowed
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import Context
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils import translation
from django.views.decorators import csrf
from django.core.urlresolvers import reverse
from django.core import exceptions as django_exceptions
from django.conf import settings
from django.contrib.auth.models import User
import askbot
import datetime
from askbot import const
from askbot.forms import SmilePayForm
from askbot.twmode import twmode as twmodeconst
from askbot.skins.loaders import render_into_skin, get_template
from askbot.models.transaction import Transaction
import logging
#jinja2 template loading enviroment

# used in index page
#todo: - take these out of const or settings
from askbot.models import Post, Vote


def Roturltest(request, **kwargs):
    smilepayform = SmilePayForm(request.POST)
    template_data = {
        'smilepayform': smilepayform,
        }

        #return render_into_skin('main_page_twmode.html', template_data, request)
    return render_into_skin('Roturltest.html', template_data, request)

def Roturl(request, **kwargs):
    """
    List of Questions, Tagged questions, and Unanswered questions.
    matching search query or user selection
    """
    if request.method == 'POST':
        smilepayform = SmilePayForm(request.POST)
        
        if smilepayform.is_valid():
            logging.info('smilepayform is valid !')
            Classif= smilepayform.cleaned_data['Classif']
            logging.debug('smilepayform Classif: %s' % (Classif)) 
            Od_sob= smilepayform.cleaned_data['Od_sob'] 
            logging.debug('smilepayform Od_sob: %s' % (Od_sob)) 
            Data_id= smilepayform.cleaned_data['Data_id'] 
            logging.debug('smilepayform Data_id: %s' % (Data_id)) 
            Process_date= smilepayform.cleaned_data['Process_date'] 
            logging.debug('smilepayform Process_date: %s' % (Process_date)) 
            Process_time= smilepayform.cleaned_data['Process_time']
            logging.debug('smilepayform Process_time: %s' % (Process_time))  
            Response_id= smilepayform.cleaned_data['Response_id'] 
            logging.debug('smilepayform Response_id: %s' % (Response_id)) 
            Auth_code= smilepayform.cleaned_data['Auth_code'] 
            logging.debug('smilepayform Auth_code: %s' % (Auth_code)) 
            LastPan= smilepayform.cleaned_data['LastPan'] 
            logging.debug('smilepayform LastPan: %s' % (LastPan)) 
            Moneytype= smilepayform.cleaned_data['Moneytype']
            logging.debug('smilepayform Moneytype: %s' % (Moneytype)) 
            Purchamt= smilepayform.cleaned_data['Purchamt'] 
            logging.debug('smilepayform Purchamt: %s' % (Purchamt)) 
            Amount= smilepayform.cleaned_data['Amount'] 
            logging.debug('smilepayform Amount: %s' % (Amount)) 
            Errdesc= smilepayform.cleaned_data['Errdesc'] 
            logging.debug('smilepayform Errdesc: %s' % (Errdesc)) 
            Pur_name= smilepayform.cleaned_data['Pur_name'] 
            logging.debug('smilepayform Pur_name: %s' % (Pur_name)) 
            Tel_number= smilepayform.cleaned_data['Tel_number'] 
            logging.debug('smilepayform Tel_number: %s' % (Tel_number)) 
            Mobile_number= smilepayform.cleaned_data['Mobile_number']
            logging.debug('smilepayform Mobile_number: %s' % (Mobile_number))  
            Address= smilepayform.cleaned_data['Address'] 
            logging.debug('smilepayform Address: %s' % (Address)) 
            Email= smilepayform.cleaned_data['Email'] 
            logging.debug('smilepayform Email: %s' % (Email)) 
            Invoice_num= smilepayform.cleaned_data['Invoice_num'] 
            logging.debug('smilepayform Invoice_num: %s' % (Invoice_num)) 
            Remark= smilepayform.cleaned_data['Remark'] 
            logging.debug('smilepayform Remark: %s' % (Remark)) 
            Smseid= smilepayform.cleaned_data['Smseid']
            logging.debug('smilepayform Smseid: %s' % (Smseid)) 
            uid=Transaction.objects.get_user_by_transactionID(Data_id)
            logging.debug('smilepayform Data_id: %s' % (Data_id)) 
            
            issue = Transaction.objects.get(id=Data_id)
            if ((issue!=None)and(issue.transaction_type==twmodeconst.TYPE_TRANSACTION_BUY_IBON_ISSUE)):
                user= User.objects.get(pk=uid)
                new_balance = user.balance + int(Amount)
                if new_balance < 0:
                    new_balance = 0 
            
    
                user.balance = new_balance
                user.save()
    
                comment = _('Receive the iBon payment confirmation.')+unicode(Amount)+_('Dollars')
                transaction = Transaction(
                            user=user,
                            income=Amount,
                            outcome=0,
                            comment=comment,
                            #question = fake_question,
                            trans_at=datetime.datetime.now(),
                            transaction_type=twmodeconst.TYPE_TRANSACTION_BUY_IBON, #todo: fix magic number
                            balance=user.balance,
                            question_id=None
                        )
    
                transaction.save()
                issue.transaction_type=twmodeconst.TYPE_TRANSACTION_BUY_IBON_ISSUE_CONFIRM 
                issue.save()
                return HttpResponse("Success!", content_type="text/plain")
            else:
                logging.warning('smilepayform warning error Date_id:%s Roturl : %s' % (Data_id,request.POST))
        else:
            logging.debug(smilepayform.errors)
            logging.debug(request.REQUEST)
    logging.debug('smilepayform error : %s' % (request.POST))
    return HttpResponse("Post Data Error.", content_type="text/plain")

def ad_model(request, **kwargs):
    """
    """
    template_data = {

        }

        #return render_into_skin('main_page_twmode.html', template_data, request)
    return render_into_skin('advertisement/model.html', template_data, request)

def FB_Channel(request, **kwargs):
    """
    """
    template_data = {

        }

        #return render_into_skin('main_page_twmode.html', template_data, request)
    return render_into_skin('FB_Channel.html', template_data, request)

def ibon(request, **kwargs):
    """
    List of Questions, Tagged questions, and Unanswered questions.
    matching search query or user selection
    """
    """if request.user.is_anonymous():
        request.user.message_set.create(message = unicode('<BR>')+_('You have to login first.')+unicode('<a href="/account/signin/?bext=/">')+_('Login Now')+unicode('</a>'))
        return HttpResponseRedirect(reverse('index'))
    """
    template_data = {

        }

        #return render_into_skin('main_page_twmode.html', template_data, request)
    return render_into_skin('payment.html', template_data, request)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def confirm(request, amount):
    """
    List of Questions, Tagged questions, and Unanswered questions.
    matching search query or user selection
    """
    if request.user.is_anonymous():
        request.user.message_set.create(message =unicode('<BR>')+ _('You have to login first.')+unicode('<a href="/account/signin/?bext=/">')+_('Login Now')+unicode('</a>'))
        return HttpResponseRedirect(reverse('index'))
    user=request.user
    comment = user.username+_('Generate iBon Barcode, USD:')+unicode(amount)+_('Dollars')
    transaction = Transaction(
                        user=user,
                        income=0,
                        outcome=0,
                        comment=comment,
                        #question = fake_question,
                        trans_at=datetime.datetime.now(),
                        transaction_type=twmodeconst.TYPE_TRANSACTION_BUY_IBON_ISSUE, #todo: fix magic number
                        balance=user.balance,
                        question_id=None
                    )

    transaction.save()
    
    template_data = {
        'Roturl': 'http://www.keepwin.com.tw/payment/Roturl/',
        'Data_id': transaction.id,             
        'amount':amount,
        'user':user,
        'ip':get_client_ip(request),
        }

        #return render_into_skin('main_page_twmode.html', template_data, request)
    return render_into_skin('payment_confirm.html', template_data, request)