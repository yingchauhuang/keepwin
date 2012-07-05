# encoding:utf-8
"""
All constants could be used in other modules
For reasons that models, views can't have unicode
text in this project, all unicode text go here. 
"""
from django.utils.translation import ugettext as _

MODERATOR_STATUS_CHOICES = (
                                ('a', _('approved')),
                                ('w', _('watched')),
                                ('s', _('suspended')),
                                ('b', _('blocked')),
                           )
ADMINISTRATOR_STATUS_CHOICES = (('d', _('administrator')),
                               ('m', _('moderator')), ) \
                               + MODERATOR_STATUS_CHOICES
                               
#Add by YC for payment and transaction
#TYPE_TRANSACTION_BUY_CREDICTCARD  = 1
#TYPE_TRANSACTION_BUY_ATM = 2
TYPE_TRANSACTION_BUY_IBON = 3
TYPE_TRANSACTION_BUY_IBON_ISSUE = 30
TYPE_TRANSACTION_BUY_IBON_ISSUE_CONFIRM = 31
TYPE_TRANSACTION_BUY_IBON_ISSUE_ERROR = 32
TYPE_TRANSACTION_BUY_CTI  = 4
#TYPE_TRANSACTION_BUY_GIFT  = 5
TYPE_TRANSACTION_PAID_FOR_CONTENT = 10
TYPE_TRANSACTION_RECEIVE_FROM_CONTENT  = 20
TYPE_TRANSACTION_SETTLE_FROM_KEEPWIN = 99
#TYPE_ACTIVITY_EDIT_ANSWER = 18

#todo: rename this to TYPE_TRANSACTION_CHOICES
TYPE_TRANSACTION = (
#    (TYPE_TRANSACTION_BUY_CREDICTCARD, _('buy bonus online via creditcard')),
#    (TYPE_TRANSACTION_BUY_ATM, _('buy bonus online via ATM')),
    (TYPE_TRANSACTION_BUY_IBON, _('buy bonus via iBon')),
    (TYPE_TRANSACTION_BUY_IBON_ISSUE, _('issue buy bonus via iBon')),
    (TYPE_TRANSACTION_BUY_CTI, _('buy bonus via Call Center Service')),
#    (TYPE_TRANSACTION_BUY_GIFT, _('buy bonus via Gift card')),
    (TYPE_TRANSACTION_PAID_FOR_CONTENT, _('paid bonus for content')),
    (TYPE_TRANSACTION_RECEIVE_FROM_CONTENT, _('receive the bonus from other people paid for it')),
    (TYPE_TRANSACTION_SETTLE_FROM_KEEPWIN, _('settle the money from keepwin')),
)

TYPE_LAYOUT_USER_DEFINE = -1
TYPE_LAYOUT_SYSTEM = 1

TYPE_LAYOUT = (
#    (TYPE_TRANSACTION_BUY_CREDICTCARD, _('buy bonus online via creditcard')),
#    (TYPE_TRANSACTION_BUY_ATM, _('buy bonus online via ATM')),
    (TYPE_LAYOUT_USER_DEFINE, _('User Define Layout')),
    (TYPE_LAYOUT_SYSTEM, _('System Layout')),
)
#user gender 
USER_GENDER_CHOICES = (
        ('m', _('male')), #male
        ('f', _('female')), #female
)
DEFAULT_GENDER_STATUS = 'f'

#user education
USER_EDUCATION_CHOICES = (
        ('e', _('elementary school')), #elementary school    
        ('j', _('junior high school')), #junior high school 
        ('h', _('high school')), #high school
        ('c', _('college')), #college
        ('g', _('graduate school')), #graduate school
        ('p', _('PhD')), #PhD
)
DEFAULT_EDUCATION_STATUS = 'g'

#user education
USER_INCOME_CHOICES = (
        ('1', _('~300K')), 
        ('2', _('300K~500K')), 
        ('3', _('500K~800K')), 
        ('4', _('800K~1000K')), 
        ('5', _('1000K~1500K')), 
        ('6', _('1500k~')), 
)
DEFAULT_INCOME_STATUS = '6'


#user occupational
USER_OCCUPATIONAL_CHOICES = (
        ('1', _('IT(Software)')), 
        ('2', _('IT(Web)')), 
        ('3', _('IT(Hardware)')), 
        ('4', _('Electricity')), 
        ('5', _('Finance')), 
        ('6', _('Education')),
        ('7', _('Civil Engineer')), 
        ('8', _('Manufacture')), 
        ('9', _('Medical')), 
        ('10', _('Law')), 
        ('11', _('Media')),  
        ('12', _('Entertainment')), 
        ('13', _('Publish')), 
        ('14', _('Travel')),  
        ('15', _('Transportation')), 
        ('16', _('Resturant')), 
        ('17', _('Department Store')),  
        ('18', _('Agent Brokerage')),
        ('19', _('NGO')),  
        ('20', _('Government')),  
        ('21', _('Military')), 
        ('22', _('Student')), 
        ('23', _('SOHO')), 
        ('24', _('Others')), 
)
DEFAULT_OCCUPATIONAL_STATUS = '1'

#user template
USER_TEMPLATE_CHOICES = (
        ('1', _('Left')), 
        ('2', _('Right')), 
)
DEFAULT_TEMPLATE_STATUS = '1'