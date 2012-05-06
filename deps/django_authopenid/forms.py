# -*- coding: utf-8 -*-
# Copyright (c) 2007, 2008, Benoît Chesneau
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#      * Redistributions of source code must retain the above copyright
#      * notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#      * notice, this list of conditions and the following disclaimer in the
#      * documentation and/or other materials provided with the
#      * distribution.  Neither the name of the <ORGANIZATION> nor the names
#      * of its contributors may be used to endorse or promote products
#      * derived from this software without specific prior written
#      * permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.conf import settings
from askbot.conf import settings as askbot_settings
from askbot import const as askbot_const
from django.utils.safestring import mark_safe
from recaptcha_works.fields import RecaptchaField
from askbot.utils.forms import NextUrlField, UserNameField, UserEmailField, SetPasswordForm

# needed for some linux distributions like debian
try:
    from openid.yadis import xri
except ImportError:
    from yadis import xri
    
from askbot.deps.django_authopenid import util

__all__ = [
    'OpenidSigninForm','OpenidRegisterForm',
    'ClassicRegisterForm', 'ChangePasswordForm',
    'ChangeEmailForm', 'EmailPasswordForm', 'DeleteForm',
    'ChangeOpenidForm'
]


#user status ch
USER_STATUS_CHOICES = (
        #in addition to these there is administrator
        #admin status is determined by the User.is_superuser() call
        ('m', _('moderator')), #user with moderation privilege
        ('a', _('approved')), #regular user
        ('w', _('watched')), #regular user placed on the moderation watch
        ('s', _('suspended')), #suspended user who cannot post new stuff
        ('b', _('blocked')), #blocked
)
DEFAULT_USER_STATUS = 'w'

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

class LoginProviderField(forms.CharField):
    """char field where value must 
    be one of login providers
    """
    widget = forms.widgets.HiddenInput()

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 64
        super(LoginProviderField, self).__init__(*args, **kwargs)

    def clean(self, value):
        """makes sure that login provider name
        exists is in the list of accepted providers
        """
        providers = util.get_enabled_login_providers()
        if value in providers:
            return value
        else:
            error_message = 'unknown provider name %s' % value
            logging.critical(error_message)
            raise forms.ValidationError(error_message)

class PasswordLoginProviderField(LoginProviderField):
    """char field where value must 
    be one of login providers using username/password
    method for authentication
    """
    def clean(self, value):
        """make sure that value is name of
        one of the known password login providers
        """
        value = super(PasswordLoginProviderField, self).clean(value)
        providers = util.get_enabled_login_providers()
        if providers[value]['type'] != 'password':
            raise forms.ValidationError(
                    'provider %s must accept password' % value
                )
        return value


class OpenidSigninForm(forms.Form):
    """ signin form """
    openid_url = forms.CharField(max_length=255, widget=forms.widgets.TextInput(attrs={'class': 'openid-login-input', 'size':80}))
    next = NextUrlField()

    def clean_openid_url(self):
        """ test if openid is accepted """
        if 'openid_url' in self.cleaned_data:
            openid_url = self.cleaned_data['openid_url']
            if xri.identifierScheme(openid_url) == 'XRI' and getattr(
                settings, 'OPENID_DISALLOW_INAMES', False
                ):
                raise forms.ValidationError(_('i-names are not supported'))
            return self.cleaned_data['openid_url']

class LoginForm(forms.Form):
    """All-inclusive login form.

    handles the following:

    * password login
    * change of password
    * openid login (of all types - direct, usename, generic url-based)
    * oauth login
    * facebook login (javascript-based facebook's sdk)
    """
    next = NextUrlField()
    login_provider_name = LoginProviderField()
    openid_login_token = forms.CharField(
                            max_length=256,
                            required = False,
                        )
    username = UserNameField(required=False, skip_clean=True)
    password = forms.CharField(
                    max_length=128, 
                    widget=forms.widgets.PasswordInput(
                                            attrs={'class':'required login'}
                                        ), 
                    required=False
                )
    password_action = forms.CharField(
                            max_length=32,
                            required=False,
                            widget=forms.widgets.HiddenInput()
                        )
    new_password = forms.CharField(
                    max_length=128, 
                    widget=forms.widgets.PasswordInput(
                                            attrs={'class':'required login'}
                                        ), 
                    required=False
                )
    new_password_retyped = forms.CharField(
                    max_length=128, 
                    widget=forms.widgets.PasswordInput(
                                            attrs={'class':'required login'}
                                        ), 
                    required=False
                )
    mobile = forms.CharField(max_length=12, 
                    label=_('Mobile'),
                    widget=forms.widgets.TextInput(
                                            attrs={'class':'required login'}
                                        ), 
                    required=False
                )
    age = forms.IntegerField(label = _('Age'),initial='30',required=False)
    gender = forms.ChoiceField(label = _('Gender'),choices=USER_GENDER_CHOICES,required=False)
    education = forms.ChoiceField(label = _('Education Background'),choices=USER_EDUCATION_CHOICES,required=False)
    income = forms.ChoiceField(label = _('Income'),choices=USER_INCOME_CHOICES,required=False)
    occupational = forms.ChoiceField(label = _('Occupational'),choices=USER_OCCUPATIONAL_CHOICES,required=False)
    SAT1 = forms.BooleanField(label = _('SAT1'), required = False) 
    SAT2 = forms.BooleanField(label = _('SAT2'), required = False) 
    SAT3 = forms.BooleanField(label = _('SAT3'), required = False) 
    SAT4 = forms.BooleanField(label = _('SAT4'), required = False) 
    SAT5 = forms.BooleanField(label = _('SAT5'), required = False) 
    SAT6 = forms.BooleanField(label = _('SAT6'), required = False) 
    SAT7 = forms.BooleanField(label = _('SAT7'), required = False) 
    SAT8 = forms.BooleanField(label = _('SAT8'), required = False) 
    SAT9 = forms.BooleanField(label = _('SAT9'), required = False) 
    SAT10= forms.BooleanField(label = _('SAT10'), required = False) 
    SAT11= forms.BooleanField(label = _('SAT11'), required = False) 
    SAT12= forms.BooleanField(label = _('SAT12'), required = False) 
    SAT13= forms.BooleanField(label = _('SAT13'), required = False) 
    SAT14= forms.BooleanField(label = _('SAT14'), required = False) 
    SAT15= forms.BooleanField(label = _('SAT15'), required = False) 
    SAT16= forms.BooleanField(label = _('SAT16'), required = False) 
    SAT17= forms.BooleanField(label = _('SAT17'), required = False) 
    SAT18= forms.BooleanField(label = _('SAT18'), required = False) 
    SAT19= forms.BooleanField(label = _('SAT19'), required = False) 
    SAT20= forms.BooleanField(label = _('SAT20'), required = False) 
    SAT21= forms.BooleanField(label = _('SAT21'), required = False) 
    SAT22= forms.BooleanField(label = _('SAT22'), required = False) 
    SAT23= forms.BooleanField(label = _('SAT23'), required = False) 
    SAT24= forms.BooleanField(label = _('SAT24'), required = False) 
    SAT25= forms.BooleanField(label = _('SAT25'), required = False)
    SAT26= forms.BooleanField(label = _('SAT26'), required = False)
    SAT27= forms.BooleanField(label = _('SAT27'), required = False) 
    SAT28= forms.BooleanField(label = _('SAT28'), required = False) 
    SAT29= forms.BooleanField(label = _('SAT29'), required = False)
    SAT30= forms.BooleanField(label = _('SAT30'), required = False) 
    SAT31= forms.BooleanField(label = _('SAT31'), required = False) 
    SAT32= forms.BooleanField(label = _('SAT32'), required = False) 
    SAT33= forms.BooleanField(label = _('SAT33'), required = False) 
    SAT34= forms.BooleanField(label = _('SAT34'), required = False) 
    SAT35= forms.BooleanField(label = _('SAT35'), required = False) 
    SAT36= forms.BooleanField(label = _('SAT36'), required = False) 
    SAT37= forms.BooleanField(label = _('SAT37'), required = False) 
    SAT38= forms.BooleanField(label = _('SAT38'), required = False) 
    SAT39= forms.BooleanField(label = _('SAT39'), required = False)
    SAT40= forms.BooleanField(label = _('SAT40'), required = False) 
    SAT41= forms.BooleanField(label = _('SAT41'), required = False) 
    SAT42= forms.BooleanField(label = _('SAT42'), required = False) 
    SAT43= forms.BooleanField(label = _('SAT43'), required = False) 
    SAT44= forms.BooleanField(label = _('SAT44'), required = False) 
    SATOther=forms.CharField(max_length=20, 
                    widget=forms.widgets.TextInput(), 
                    required=False)
    def set_error_if_missing(self, field_name, error_message):
        """set's error message on a field
        if the field is not present in the cleaned_data dictionary
        """
        if field_name not in self.cleaned_data:
            self._errors[field_name] = self.error_class([error_message])

    def set_password_login_error(self):
        """sets a parameter flagging that login with
        password had failed
        """
        #add monkey-patch parameter
        #this is used in the signin.html template
        self.password_login_failed = True

    def set_password_change_error(self):
        """sets a parameter flagging that
        password change failed
        """
        #add monkey-patch parameter
        #this is used in the signin.html template
        self.password_change_failed = True


    def clean(self):
        """besides input data takes data from the
        login provider settings
        and stores final digested data into
        the cleaned_data

        the idea is that cleaned data can be used directly
        to enact the signin action, without post-processing
        of the data

        contents of cleaned_data depends on the type
        of login
        """
        providers = util.get_enabled_login_providers()

        if 'login_provider_name' in self.cleaned_data:
            provider_name = self.cleaned_data['login_provider_name']
        else:
            raise forms.ValidationError('no login provider specified')

        provider_data = providers[provider_name]

        provider_type = provider_data['type']

        if provider_type == 'password':
            self.do_clean_password_fields()
            self.cleaned_data['login_type'] = 'password'
        elif provider_type.startswith('openid'):
            self.do_clean_openid_fields(provider_data)
            self.cleaned_data['login_type'] = 'openid'
        elif provider_type == 'oauth':
            self.cleaned_data['login_type'] = 'oauth'
            pass
        elif provider_type == 'facebook':
            self.cleaned_data['login_type'] = 'facebook'
            #self.do_clean_oauth_fields()
        elif provider_type == 'wordpress_site':
            self.cleaned_data['login_type'] = 'wordpress_site'

        return self.cleaned_data

    def do_clean_openid_fields(self, provider_data):
        """returns fake openid_url value
        created based on provider_type (subtype of openid)
        and the
        """
        openid_endpoint = provider_data['openid_endpoint']
        openid_type = provider_data['type']
        if openid_type == 'openid-direct':
            openid_url = openid_endpoint
        else:
            error_message = _('Please enter your %(username_token)s') % \
                    {'username_token': provider_data['extra_token_name']}
            self.set_error_if_missing('openid_login_token', error_message)
            if 'openid_login_token' in self.cleaned_data:
                openid_login_token = self.cleaned_data['openid_login_token']

                if openid_type == 'openid-username':
                    openid_url = openid_endpoint % {'username': openid_login_token}
                elif openid_type == 'openid-generic':
                    openid_url = openid_login_token
                else:
                    raise ValueError('unknown openid type %s' % openid_type)

        self.cleaned_data['openid_url'] = openid_url

    def do_clean_password_fields(self):
        """cleans password fields appropriate for
        the selected password_action, which can be either
        "login" or "change_password"
        new password is checked for minimum length and match to initial entry
        """
        password_action = self.cleaned_data.get('password_action', None)
        if password_action == 'login':
            #if it's login with password - password and user name are required
            self.set_error_if_missing(
                'username',
                _('Please, enter your user name')
            )
            self.set_error_if_missing(
                'password',
                _('Please, enter your password')
            )

        elif password_action == 'change_password':
            #if it's change password - new_password and new_password_retyped
            self.set_error_if_missing(
                'new_password',
                 _('Please, enter your new password')
            ) 
            self.set_error_if_missing(
                'new_password_retyped',
                _('Please, enter your new password')
            )
            field_set = set(('new_password', 'new_password_retyped'))
            if field_set.issubset(self.cleaned_data.keys()):
                new_password = self.cleaned_data[
                                                'new_password'
                                            ].strip()
                new_password_retyped = self.cleaned_data[
                                                'new_password_retyped'
                                            ].strip()
                if new_password != new_password_retyped:
                    error_message = _('Passwords did not match')
                    error = self.error_class([error_message])
                    self._errors['new_password_retyped'] = error
                    self.set_password_change_error()
                    del self.cleaned_data['new_password']
                    del self.cleaned_data['new_password_retyped']
                else:
                    #validate password
                    if len(new_password) < askbot_const.PASSWORD_MIN_LENGTH:
                        del self.cleaned_data['new_password']
                        del self.cleaned_data['new_password_retyped']
                        error_message = _(
                                    'Please choose password > %(len)s characters'
                                ) % {'len': askbot_const.PASSWORD_MIN_LENGTH}
                        error = self.error_class([error_message])
                        self._errors['new_password'] = error
                        self.set_password_change_error()
        else:
            error_message = 'unknown password action'
            logging.critical(error_message)
            self._errors['password_action'] = self.error_class([error_message])
            raise forms.ValidationError(error_message)

class OpenidRegisterForm(forms.Form):
    """ openid signin form """
    next = NextUrlField()
    username = UserNameField()
    email = UserEmailField()

class ClassicRegisterForm(SetPasswordForm):
    """ legacy registration form """

    next = NextUrlField()
    username = UserNameField()
    email = UserEmailField()
    login_provider = PasswordLoginProviderField()
    #fields password1 and password2 are inherited

class SafeClassicRegisterForm(ClassicRegisterForm):
    """this form uses recaptcha in addition
    to the base register form
    """
    recaptcha = RecaptchaField(
                    private_key = askbot_settings.RECAPTCHA_SECRET,
                    public_key = askbot_settings.RECAPTCHA_KEY
                )

class ChangePasswordForm(SetPasswordForm):
    """ change password form """
    oldpw = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required'}),
                label=mark_safe(_('Current password')))

    def __init__(self, data=None, user=None, *args, **kwargs):
        if user is None:
            raise TypeError("Keyword argument 'user' must be supplied")
        super(ChangePasswordForm, self).__init__(data, *args, **kwargs)
        self.user = user

    def clean_oldpw(self):
        """ test old password """
        if not self.user.check_password(self.cleaned_data['oldpw']):
            raise forms.ValidationError(_("Old password is incorrect. \
                    Please enter the correct password."))
        return self.cleaned_data['oldpw']

class ChangeEmailForm(forms.Form):
    """ change email form """
    email = UserEmailField(skip_clean=True)

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, \
            initial=None, user=None):
        super(ChangeEmailForm, self).__init__(data, files, auto_id, 
                prefix, initial)
        self.user = user

    def clean_email(self):
        """ check if email don't exist """
        if 'email' in self.cleaned_data:
            if askbot_settings.EMAIL_UNIQUE == True:
                try:
                    user = User.objects.get(email = self.cleaned_data['email'])
                    if self.user and self.user == user:   
                        return self.cleaned_data['email']
                except User.DoesNotExist:
                    return self.cleaned_data['email']
                except User.MultipleObjectsReturned:
                    raise forms.ValidationError(u'There is already more than one \
                        account registered with that e-mail address. Please try \
                        another.')
                raise forms.ValidationError(u'This email is already registered \
                    in our database. Please choose another.')
            else:
                return self.cleaned_data['email']

class AccountRecoveryForm(forms.Form):
    """with this form user enters email address and
    receives an account recovery link in email

    this form merely checks that entered email
    """
    email = forms.EmailField()

    def clean_email(self):
        """check if email exists in the database
        and if so, populate 'user' field in the cleaned data
        with the user object
        """
        if 'email' in self.cleaned_data:
            email = self.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                self.cleaned_data['user'] = user
            except User.DoesNotExist:
                del self.cleaned_data['email']
                message = _('Sorry, we don\'t have this email address in the database')
                raise forms.ValidationError(message)
        
class ChangeopenidForm(forms.Form):
    """ change openid form """
    openid_url = forms.CharField(max_length=255,
            widget=forms.TextInput(attrs={'class': "required" }))

    def __init__(self, data=None, user=None, *args, **kwargs):
        if user is None:
            raise TypeError("Keyword argument 'user' must be supplied")
        super(ChangeopenidForm, self).__init__(data, *args, **kwargs)
        self.user = user

class DeleteForm(forms.Form):
    """ confirm form to delete an account """
    #todo: i think this form is not used
    confirm = forms.CharField(widget=forms.CheckboxInput(attrs={'class':'required'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required'}))

    def __init__(self, data=None, files=None, auto_id='id_%s',
            prefix=None, initial=None, user=None):
        super(DeleteForm, self).__init__(data, files, auto_id, prefix, initial)
        self.test_openid = False
        self.user = user

    def clean_password(self):
        """ check if we have to test a legacy account or not """
        if 'password' in self.cleaned_data:
            if not self.user.check_password(self.cleaned_data['password']):
                self.test_openid = True
        return self.cleaned_data['password']


class EmailPasswordForm(forms.Form):
    """ send new password form """
    username = UserNameField(skip_clean=True,label=mark_safe(_('Your user name (<i>required</i>)')))

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, 
            initial=None):
        super(EmailPasswordForm, self).__init__(data, files, auto_id, 
                prefix, initial)
        self.user_cache = None

    def clean_username(self):
        """ get user for this username """
        if 'username' in self.cleaned_data:
            try:
                self.user_cache = User.objects.get(
                        username = self.cleaned_data['username'])
            except:
                raise forms.ValidationError(_("Incorrect username."))
        return self.cleaned_data['username']
