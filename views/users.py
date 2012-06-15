"""
:synopsis: user-centric views for askbot

This module includes all views that are specific to a given user - his or her profile,
and other views showing profile-related information.

Also this module includes the view listing all forum users.
"""
import calendar
import collections
import functools
import datetime
from datetime import datetime as Cdatetime
import logging
import operator
import sys
from decimal import *
from django.db.models import Count, Q
from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.http import HttpResponseRedirect, Http404
from django.utils.translation import ugettext as _
from django.utils import simplejson
from django.views.decorators import csrf

from askbot.utils.slug import slugify
from askbot.utils.html import sanitize_html
from askbot.utils.mail import send_mail
from askbot.utils.http import get_request_info
from askbot.utils import functions
from askbot import forms
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot import models
from askbot import exceptions
from askbot.models.badges import award_badges_signal
from askbot.skins.loaders import render_into_skin
from askbot.templatetags import extra_tags
from askbot.search.state_manager import SearchState
from askbot.models import Post
from askbot.models.user import UserInfo
from askbot.models.profilelayout import UserProfileLayout,ProfileLayout,UserProfileLayoutManager

def owner_or_moderator_required(f):
    @functools.wraps(f)
    def wrapped_func(request, profile_owner, context):
        if profile_owner == request.user:
            pass
        elif request.user.is_authenticated() and request.user.can_moderate_user(profile_owner):
            pass
        else:
            params = '?next=%s' % request.path
            return HttpResponseRedirect(reverse('user_signin') + params)
        return f(request, profile_owner, context)
    return wrapped_func

def users(request):
    is_paginated = True
    sortby = request.GET.get('sort', 'reputation')
    suser = request.REQUEST.get('query',  "")
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    if suser == "":
        if sortby == "newest":
            order_by_parameter = '-date_joined'
        elif sortby == "last":
            order_by_parameter = 'date_joined'
        elif sortby == "user":
            order_by_parameter = 'username'
        else:
            # default
            order_by_parameter = '-reputation'

        objects_list = Paginator(
                            models.User.objects.filter(status__in=['d','m']).order_by(
                                                order_by_parameter
                                            ),
                            const.USERS_PAGE_SIZE
                        )
        base_url = reverse('users') + '?sort=%s&' % sortby
    else:
        sortby = "reputation"
        objects_list = Paginator(
                            models.User.objects.filter(
                                                username__icontains = suser
                                            ).order_by(
                                                '-reputation'
                                            ),
                            const.USERS_PAGE_SIZE
                        )
        base_url = reverse('users') + '?name=%s&sort=%s&' % (suser, sortby)

    try:
        users_page = objects_list.page(page)
    except (EmptyPage, InvalidPage):
        users_page = objects_list.page(objects_list.num_pages)

    paginator_data = {
        'is_paginated' : is_paginated,
        'pages': objects_list.num_pages,
        'page': page,
        'has_previous': users_page.has_previous(),
        'has_next': users_page.has_next(),
        'previous': users_page.previous_page_number(),
        'next': users_page.next_page_number(),
        'base_url' : base_url
    }
    paginator_context = functions.setup_paginator(paginator_data) #
    data = {
        'active_tab': 'users',
        'page_class': 'users-page',
        'users' : users_page,
        'suser' : suser,
        'keywords' : suser,
        'tab_id' : sortby,
        'paginator_context' : paginator_context
    }
    return render_into_skin('users.html', data, request)

def users_admin(request):
    is_paginated = True
    sortby = request.GET.get('sort', 'reputation')
    suser = request.REQUEST.get('query',  "")
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    if suser == "":
        if sortby == "newest":
            order_by_parameter = '-date_joined'
        elif sortby == "last":
            order_by_parameter = 'date_joined'
        elif sortby == "user":
            order_by_parameter = 'username'
        else:
            # default
            order_by_parameter = '-reputation'

        objects_list = Paginator(
                            models.User.objects.all().order_by(
                                                order_by_parameter
                                            ),
                            const.USERS_PAGE_SIZE
                        )
        base_url = reverse('users_admin') + '?sort=%s&' % sortby
    else:
        sortby = "reputation"
        objects_list = Paginator(
                            models.User.objects.filter(
                                                username__icontains = suser
                                            ).order_by(
                                                '-reputation'
                                            ),
                            const.USERS_PAGE_SIZE
                        )
        base_url = reverse('users_admin') + '?name=%s&sort=%s&' % (suser, sortby)

    try:
        users_page = objects_list.page(page)
    except (EmptyPage, InvalidPage):
        users_page = objects_list.page(objects_list.num_pages)

    paginator_data = {
        'is_paginated' : is_paginated,
        'pages': objects_list.num_pages,
        'page': page,
        'has_previous': users_page.has_previous(),
        'has_next': users_page.has_next(),
        'previous': users_page.previous_page_number(),
        'next': users_page.next_page_number(),
        'base_url' : base_url
    }
    paginator_context = functions.setup_paginator(paginator_data) #
    data = {
        'active_tab': 'users_admin',
        'page_class': 'users-page',
        'users' : users_page,
        'suser' : suser,
        'keywords' : suser,
        'tab_id' : sortby,
        'paginator_context' : paginator_context
    }
    return render_into_skin('users_admin.html', data, request)

@csrf.csrf_protect
def user_moderate(request, subject, context):
    """user subview for moderation
    """
    moderator = request.user

    if not moderator.can_moderate_user(subject):
        raise Http404

    user_rep_changed = False
    user_status_changed = False
    message_sent = False
    email_error_message = None

    user_rep_form = forms.ChangeUserReputationForm()
    send_message_form = forms.SendMessageForm()
    if request.method == 'POST':
        if 'change_status' in request.POST:
            user_status_form = forms.ChangeUserStatusForm(
                                                    request.POST,
                                                    moderator = moderator,
                                                    subject = subject
                                                )
            if user_status_form.is_valid():
                subject.set_status( user_status_form.cleaned_data['user_status'] )
            user_status_changed = True
        elif 'send_message' in request.POST:
            send_message_form = forms.SendMessageForm(request.POST)
            if send_message_form.is_valid():
                subject_line = send_message_form.cleaned_data['subject_line']
                body_text = send_message_form.cleaned_data['body_text']

                try:
                    send_mail(
                            subject_line = subject_line,
                            body_text = body_text,
                            recipient_list = [subject.email],
                            headers={'Reply-to':moderator.email},
                            raise_on_failure = True
                        )
                    message_sent = True
                except exceptions.EmailNotSent, e:
                    email_error_message = unicode(e)
                send_message_form = forms.SendMessageForm()
        else:
            reputation_change_type = None
            if 'subtract_reputation' in request.POST:
                rep_change_type = 'subtract'
            elif 'add_reputation' in request.POST:
                rep_change_type = 'add'
            else:
                raise Http404

            user_rep_form = forms.ChangeUserReputationForm(request.POST)
            if user_rep_form.is_valid():
                rep_delta = user_rep_form.cleaned_data['user_reputation_delta']
                comment = user_rep_form.cleaned_data['comment']

                if rep_change_type == 'subtract':
                    rep_delta = -1 * rep_delta

                moderator.moderate_user_reputation(
                                    user = subject,
                                    reputation_change = rep_delta,
                                    comment = comment,
                                    timestamp = datetime.datetime.now(),
                                )
                #reset form to preclude accidentally repeating submission
                user_rep_form = forms.ChangeUserReputationForm()
                user_rep_changed = True

    #need to re-initialize the form even if it was posted, because
    #initial values will most likely be different from the previous
    user_status_form = forms.ChangeUserStatusForm(
                                        moderator = moderator,
                                        subject = subject
                                    )
    data = {
        'active_tab': 'users',
        'page_class': 'user-profile-page',
        'tab_name': 'moderate user role',
        'tab_description': _('moderate this user'),
        'page_title': _('moderate user role'),
        'change_user_status_form': user_status_form,
        'change_user_reputation_form': user_rep_form,
        'send_message_form': send_message_form,
        'message_sent': message_sent,
        'email_error_message': email_error_message,
        'user_rep_changed': user_rep_changed,
        'user_status_changed': user_status_changed
    }
    context.update(data)
    return render_into_skin('user_profile/user_moderate.html', context, request)

def save_template(request):
    if request.method == "POST":
        try:
            main_template = request.POST['main_template']
            sidebar_template = request.POST['sidebar_template']
            user = request.user
            user.main_template=main_template
            user.sidebar_template=sidebar_template 
            user.save()
            data = simplejson.dumps({
                'success': True,
                'message': _('Your config is saved')
            })
        except:
            data = simplejson.dumps({
                'success': False,
                'message': _('Save Template Error')
            })
    else:
        data = simplejson.dumps({
                'success': False,
                'message': _('Save Template Error-- Please use post')
            })
    return HttpResponse(data, mimetype = 'application/json')

def update_template_content(request):
    if request.method == "POST":
        try:
            template_id = request.POST['id']
            content = request.POST['content']
            title = request.POST['title']
            if (UserProfileLayout.objects.update_template(userprofilelayoutid=template_id,content=content,title=title)):
                data = simplejson.dumps({
                    'message': _('successful update template content'),
                    'id': template_id,
                    'title': title,
                    'content': content,
                    'success': True,
                })
            else:    
                data = simplejson.dumps({
                    'message': _('update template content failure.'),
                    'id': template_id,
                    'title': title,
                    'content': content,
                    'success': False,
                })

        except:
            data = simplejson.dumps({
                'message': _('update template content failure.')+sys.exc_info()[0],
                'id': template_id,
                'title': title,
                'content': content,
                'success': False,
            })
    return HttpResponse(data, mimetype = 'application/json')


def add_template(request):
    is_new=False
    if request.method == "POST":
        try:
            template_id = request.POST['id']
            user = request.user
            newtemplate, is_new=user.add_template(template_id,'')
            if (is_new):
                user.main_template=user.main_template+','+unicode(newtemplate.id)
                user.save()
                data = simplejson.dumps({
                    'message': _('successful add a template'),
                    'id': newtemplate.id,
                    'type': newtemplate.profilelayout.layout_type,
                    'is_new': is_new,
                })
            else:    
                data = simplejson.dumps({
                    'message': _('You have added a template already.'),
                    'id': newtemplate.id,
                    'type': newtemplate.profilelayout.layout_type,
                    'is_new': is_new,
                })

        except:
            data = simplejson.dumps({
                'message': sys.exc_info()[0],
                'id': '',
                'type': 1,
                'is_new': is_new,
            })
    return HttpResponse(data, mimetype = 'application/json')

def delete_template(request):
    if request.method == "POST":
        try:
            template_id = request.POST['id']
            user = request.user
            user.delete_template(template_id)
            
            data = simplejson.dumps({
                'message': 'You have deleted template',
                'id': template_id,
                'success': True,
            })
        except:
            data = simplejson.dumps({
                'message': sys.exc_info()[0],
                'id;: template_id ,'
                'success': False,
            })
    return HttpResponse(data, mimetype = 'application/json')

@csrf.csrf_protect
def user_layout(request, subject, context):
    """user layout
    """
    user_layout_form = forms.UserLayoutForm()
    user = request.user
    profilelayouts = ProfileLayout.objects.all()
    userprofilelayouts = UserProfileLayout.objects.filter(user=user)

    main_list = list()
    sidebar_list= list()
    main_id_list = user.main_template.split(',')
    sidebar_id_list = user.sidebar_template.split(',')

    for id in main_id_list:
        try:
            layout=userprofilelayouts.get(id=id)
            main_list.append(layout)
        except:
            logging.debug('Error in main_id_list: %s' % ','.join(unicode(id)))
        
    for id in sidebar_id_list:
        try:
            layout=userprofilelayouts.get(id=id)
            sidebar_list.append(layout)
        except:
            logging.debug('Error in sidebar_id_list: %s' % ','.join(unicode(id)))
                    
    if request.method == 'POST':
            user_layout_form = forms.UserLayoutForm(request.POST)
            if user_layout_form.is_valid():
                user_layout = user_layout_form.cleaned_data['layout']


    #need to re-initialize the form even if it was posted, because
    #initial values will most likely be different from the previous

    data = {
        'active_tab': 'users',
        'page_class': 'user-profile-page',
        'tab_name':  _('layout'),
        'tab_description': _('change user default page layout'),
        'page_title': _('profile - layout'),
        'user_layout_form': user_layout_form,
        'profilelayouts' : profilelayouts,
        'main_list': main_list,
        'sidebar_list': sidebar_list,

    }
    context.update(data)
    return render_into_skin('user_profile/user_layout.html', context, request)

@csrf.csrf_protect
def user_add_transaction(request, subject, context):
    """user subview for moderation
    """
    moderator = request.user

    if not moderator.can_moderate_user(subject):
        raise Http404

    user_transaction_added  = False
    message_sent = False
    email_error_message = None

    user_transaction_form = forms.AddUserTransactionForm()
    send_message_form = forms.SendMessageForm()
    if request.method == 'POST':
        if 'send_message' in request.POST:
            send_message_form = forms.SendMessageForm(request.POST)
            if send_message_form.is_valid():
                subject_line = send_message_form.cleaned_data['subject_line']
                body_text = send_message_form.cleaned_data['body_text']

                try:
                    send_mail(
                            subject_line = subject_line,
                            body_text = body_text,
                            recipient_list = [subject.email],
                            headers={'Reply-to':moderator.email},
                            raise_on_failure = True
                        )
                    message_sent = True
                except exceptions.EmailNotSent, e:
                    email_error_message = unicode(e)
                send_message_form = forms.SendMessageForm()
        else:
            transaction_change_type = None

            user_transaction_form = forms.AddUserTransactionForm(request.POST)
            if user_transaction_form.is_valid():
                user_income = user_transaction_form.cleaned_data['user_income']
                user_outcome = user_transaction_form.cleaned_data['user_outcome']
                transaction_type = user_transaction_form.cleaned_data['transaction_type'] 
                comment = user_transaction_form.cleaned_data['comment']

                moderator.add_user_transaction(
                                    user = subject,
                                    income =user_income,
                                    outcome =user_outcome,
                                    transaction_type=transaction_type,
                                    comment = comment,
                                    timestamp = datetime.datetime.now()
                                )
                #reset form to preclude accidentally repeating submission
                user_transaction_form = forms.AddUserTransactionForm()
                user_transaction_added = True

    #need to re-initialize the form even if it was posted, because
    #initial values will most likely be different from the previous

    data = {
        'active_tab': 'users',
        'page_class': 'user-profile-page',
        'tab_name': 'addtransaction',
        'tab_description': _('add transaction to modify user balance'),
        'page_title': _('add transaction'),
        'add_user_transaction_form': user_transaction_form,
        'send_message_form': send_message_form,
        'message_sent': message_sent,
        'email_error_message': email_error_message,
        'user_transaction_added': user_transaction_added,
    }
    context.update(data)
    return render_into_skin('user_profile/user_add_transaction.html', context, request)

#non-view function
def set_new_email(user, new_email, nomessage=False):
    if new_email != user.email:
        user.email = new_email
        user.email_isvalid = False
        user.save()
        #if askbot_settings.EMAIL_VALIDATION == True:
        #    send_new_email_key(user,nomessage=nomessage)

@login_required
@csrf.csrf_protect
def edit_user(request, id):
    """View that allows to edit user profile.
    This view is accessible to profile owners or site administrators
    """
    user = get_object_or_404(models.User, id=id)
    if not(request.user == user or request.user.is_superuser):
        raise Http404
    if request.method == "POST":
        form = forms.EditUserForm(user, request.POST)
        if form.is_valid():
            new_email = sanitize_html(form.cleaned_data['email'])

            set_new_email(user, new_email)

            if askbot_settings.EDITABLE_SCREEN_NAME:
                user.username = sanitize_html(form.cleaned_data['username'])

            user.real_name = sanitize_html(form.cleaned_data['realname'])
            user.website = sanitize_html(form.cleaned_data['website'])
            user.location = sanitize_html(form.cleaned_data['city'])
            user.date_of_birth = form.cleaned_data.get('birthday', None)
            user.about = form.cleaned_data['about']
            user.country = form.cleaned_data['country']
            user.show_country = form.cleaned_data['show_country']

            user.save()
            
            userinfo = UserInfo.objects.get(user=user)
            userinfo.mobile = form.cleaned_data['mobile']
            #userinfo.age = form.cleaned_data['age']
            userinfo.gender = form.cleaned_data['gender']
            userinfo.education = form.cleaned_data['education']
            userinfo.income = form.cleaned_data['income']
            userinfo.occupational = form.cleaned_data['occupational']
            
            userinfo.SAT1 = form.cleaned_data['SAT1']
            userinfo.SAT2 = form.cleaned_data['SAT2']
            userinfo.SAT3 = form.cleaned_data['SAT3']
            userinfo.SAT4 = form.cleaned_data['SAT4']
            userinfo.SAT5 = form.cleaned_data['SAT5']
            userinfo.SAT6 = form.cleaned_data['SAT6']
            userinfo.SAT7 = form.cleaned_data['SAT7']
            userinfo.SAT8 = form.cleaned_data['SAT8']
            userinfo.SAT9 = form.cleaned_data['SAT9']
            userinfo.SAT10 = form.cleaned_data['SAT10']
            userinfo.SAT11 = form.cleaned_data['SAT11']
            userinfo.SAT12 = form.cleaned_data['SAT12']
            userinfo.SAT13 = form.cleaned_data['SAT13']
            userinfo.SAT14 = form.cleaned_data['SAT14']
            userinfo.SAT15 = form.cleaned_data['SAT15']
            userinfo.SAT16 = form.cleaned_data['SAT16']
            userinfo.SAT17 = form.cleaned_data['SAT17']
            userinfo.SAT18 = form.cleaned_data['SAT18']
            userinfo.SAT19 = form.cleaned_data['SAT19']
            userinfo.SAT20 = form.cleaned_data['SAT20']
            userinfo.SAT21 = form.cleaned_data['SAT21']
            userinfo.SAT22 = form.cleaned_data['SAT22']
            userinfo.SAT23 = form.cleaned_data['SAT23']
            userinfo.SAT24 = form.cleaned_data['SAT24']
            userinfo.SAT25 = form.cleaned_data['SAT25']
            userinfo.SAT26 = form.cleaned_data['SAT26']
            userinfo.SAT27 = form.cleaned_data['SAT27']
            userinfo.SAT28 = form.cleaned_data['SAT28']
            userinfo.SAT29 = form.cleaned_data['SAT29']
            userinfo.SAT30 = form.cleaned_data['SAT30']
            userinfo.SAT31 = form.cleaned_data['SAT31']
            userinfo.SAT32 = form.cleaned_data['SAT32']
            userinfo.SAT33 = form.cleaned_data['SAT33']
            userinfo.SAT34 = form.cleaned_data['SAT34']
            userinfo.SAT35 = form.cleaned_data['SAT35']
            userinfo.SAT36 = form.cleaned_data['SAT36']
            userinfo.SAT37 = form.cleaned_data['SAT37']
            userinfo.SAT38 = form.cleaned_data['SAT38']
            userinfo.SAT39 = form.cleaned_data['SAT39']
            userinfo.SAT40 = form.cleaned_data['SAT40']
            userinfo.SAT41 = form.cleaned_data['SAT41']
            userinfo.SAT42 = form.cleaned_data['SAT42']
            userinfo.SAT43 = form.cleaned_data['SAT43']
            userinfo.SAT44 = form.cleaned_data['SAT44']
            userinfo.SATOther = form.cleaned_data['SATOther']
            userinfo.save()
            # send user updated signal if full fields have been updated
            award_badges_signal.send(None,
                            event = 'update_user_profile',
                            actor = user,
                            context_object = user
                        )
            return HttpResponseRedirect(user.get_profile_url())
    else:
        form = forms.EditUserForm(user)
    data = {
        'active_tab': 'users',
        'page_class': 'user-profile-edit-page',
        'form' : form,
        'support_custom_avatars': ('avatar' in django_settings.INSTALLED_APPS),
        'view_user': user,
    }
    return render_into_skin('user_profile/user_edit.html', data, request)

def user_stats(request, user, context):
    question_filter = {}
    if request.user != user:
        question_filter['is_anonymous'] = False

    #
    # Questions
    #
    questions = user.posts.get_questions().filter(**question_filter).\
                    order_by('-score', '-thread__last_activity_at').\
                    select_related('thread', 'thread__last_activity_by')[:100]

    #added this if to avoid another query if questions is less than 100
    if len(questions) < 100:
        question_count = len(questions)
    else:
        question_count = user.posts.get_questions().filter(**question_filter).count()

    #
    # Top answers
    #
    top_answers = user.posts.get_answers().filter(
        deleted=False,
        thread__posts__deleted=False,
        thread__posts__post_type='question',
    ).select_related('thread').order_by('-score', '-added_at')[:100]

    top_answer_count = len(top_answers)

    #
    # Votes
    #
    up_votes = models.Vote.objects.get_up_vote_count_from_user(user)
    down_votes = models.Vote.objects.get_down_vote_count_from_user(user)
    votes_today = models.Vote.objects.get_votes_count_today_from_user(user)
    votes_total = askbot_settings.MAX_VOTES_PER_USER_PER_DAY

    #
    # Tags
    #
    # INFO: There's bug in Django that makes the following query kind of broken (GROUP BY clause is problematic):
    #       http://stackoverflow.com/questions/7973461/django-aggregation-does-excessive-group-by-clauses
    #       Fortunately it looks like it returns correct results for the test data
    user_tags = models.Tag.objects.filter(threads__posts__author=user).distinct().\
                    annotate(user_tag_usage_count=Count('threads')).\
                    order_by('-user_tag_usage_count')[:const.USER_VIEW_DATA_SIZE]
    user_tags = list(user_tags) # evaluate

#    tags = models.Post.objects.filter(author=user).values('id', 'thread', 'thread__tags')
#    post_ids = set()
#    thread_ids = set()
#    tag_ids = set()
#    for t in tags:
#        post_ids.add(t['id'])
#        thread_ids.add(t['thread'])
#        tag_ids.add(t['thread__tags'])
#        if t['thread__tags'] == 11:
#            print t['thread'], t['id']
#    import ipdb; ipdb.set_trace()

    #
    # Badges/Awards (TODO: refactor into Managers/QuerySets when a pattern emerges; Simplify when we get rid of Question&Answer models)
    #
    post_type = ContentType.objects.get_for_model(models.Post)

    user_awards = models.Award.objects.filter(user=user).select_related('badge')

    awarded_post_ids = []
    for award in user_awards:
        if award.content_type_id == post_type.id:
            awarded_post_ids.append(award.object_id)

    awarded_posts = models.Post.objects.filter(id__in=awarded_post_ids)\
                    .select_related('thread') # select related to avoid additional queries in Post.get_absolute_url()

    awarded_posts_map = {}
    for post in awarded_posts:
        awarded_posts_map[post.id] = post

    badges_dict = collections.defaultdict(list)

    for award in user_awards:
        # Fetch content object
        try:
            if award.content_type_id == post_type.id:
                award.content_object = awarded_posts_map[award.object_id]
                award.content_object_is_post = True
            else:
                award.content_object_is_post = False
    
            # "Assign" to its Badge
            badges_dict[award.badge].append(award)
        except:
            pass
    badges = badges_dict.items()
    badges.sort(key=operator.itemgetter(1), reverse=True)

    data = {
        'active_tab':'users',
        'page_class': 'user-profile-page',
        'support_custom_avatars': ('avatar' in django_settings.INSTALLED_APPS),
        'tab_name' : 'stats',
        'tab_description' : _('user profile'),
        'page_title' : _('user profile overview'),
        'user_status_for_display': user.get_status_display(soft = True),
        'questions' : questions,
        'questions_count': question_count,

        'top_answers': top_answers,
        'top_answer_count': top_answer_count,

        'up_votes' : up_votes,
        'down_votes' : down_votes,
        'total_votes': up_votes + down_votes,
        'votes_today_left': votes_total - votes_today,
        'votes_total_per_day': votes_total,

        'user_tags' : user_tags,

        'badges': badges,
        'total_badges' : len(badges),
    }
    context.update(data)

    return render_into_skin('user_profile/user_stats.html', context, request)

def user_stats_vip(request, user, context):
    question_filter = {}
    if request.user != user:
        question_filter['is_anonymous'] = False
    question_filter['deleted'] = False
    #
    # Questions
    #
    questions = user.posts.get_questions().filter(**question_filter).\
                    order_by('-score', '-thread__last_activity_at').\
                    select_related('thread', 'thread__last_activity_by')[:100]

    #added this if to avoid another query if questions is less than 100
    if len(questions) < 100:
        question_count = len(questions)
    else:
        question_count = user.posts.get_questions().filter(**question_filter).count()

    #
    # Top answers
    #
    top_answers = user.posts.get_answers().filter(
        deleted=False,
        thread__posts__deleted=False,
        thread__posts__post_type='question',
    ).select_related('thread').order_by('-score', '-added_at')[:100]

    top_answer_count = len(top_answers)

    #
    # Votes
    #
    up_votes = models.Vote.objects.get_up_vote_count_from_user(user)
    down_votes = models.Vote.objects.get_down_vote_count_from_user(user)
    votes_today = models.Vote.objects.get_votes_count_today_from_user(user)
    votes_total = askbot_settings.MAX_VOTES_PER_USER_PER_DAY

    #
    # Tags
    #
    # INFO: There's bug in Django that makes the following query kind of broken (GROUP BY clause is problematic):
    #       http://stackoverflow.com/questions/7973461/django-aggregation-does-excessive-group-by-clauses
    #       Fortunately it looks like it returns correct results for the test data
    user_tags = models.Tag.objects.filter(threads__posts__author=user).distinct().\
                    annotate(user_tag_usage_count=Count('threads')).\
                    order_by('-user_tag_usage_count')[:const.USER_VIEW_DATA_SIZE]
    user_tags = list(user_tags) # evaluate

#    tags = models.Post.objects.filter(author=user).values('id', 'thread', 'thread__tags')
#    post_ids = set()
#    thread_ids = set()
#    tag_ids = set()
#    for t in tags:
#        post_ids.add(t['id'])
#        thread_ids.add(t['thread'])
#        tag_ids.add(t['thread__tags'])
#        if t['thread__tags'] == 11:
#            print t['thread'], t['id']
#    import ipdb; ipdb.set_trace()

    #
    # Badges/Awards (TODO: refactor into Managers/QuerySets when a pattern emerges; Simplify when we get rid of Question&Answer models)
    #
    post_type = ContentType.objects.get_for_model(models.Post)

    user_awards = models.Award.objects.filter(user=user).select_related('badge')

    awarded_post_ids = []
    for award in user_awards:
        if award.content_type_id == post_type.id:
            awarded_post_ids.append(award.object_id)

    awarded_posts = models.Post.objects.filter(id__in=awarded_post_ids)\
                    .select_related('thread') # select related to avoid additional queries in Post.get_absolute_url()

    awarded_posts_map = {}
    for post in awarded_posts:
        awarded_posts_map[post.id] = post

    badges_dict = collections.defaultdict(list)

    for award in user_awards:
        # Fetch content object
        if award.content_type_id == post_type.id:
            award.content_object = awarded_posts_map[award.object_id]
            award.content_object_is_post = True
        else:
            award.content_object_is_post = False

        # "Assign" to its Badge
        badges_dict[award.badge].append(award)

    badges = badges_dict.items()
    badges.sort(key=operator.itemgetter(1), reverse=True)
    
    userprofilelayouts = UserProfileLayout.objects.filter(user=user)

    main_list = list()
    sidebar_list= list()
    main_id_list = user.main_template.split(',')
    sidebar_id_list = user.sidebar_template.split(',')

    for id in main_id_list:
        try:
            layout=userprofilelayouts.get(id=id)
            main_list.append(layout)
        except:
            logging.debug('Error in main_id_list: %s' % ','.join(unicode(id)))
        
    for id in sidebar_id_list:
        try:
            layout=userprofilelayouts.get(id=id)
            sidebar_list.append(layout)
        except:
            logging.debug('Error in sidebar_id_list: %s' % ','.join(unicode(id)))

    data = {
        'active_tab':'users',
        'page_class': 'user-profile-page',
        'support_custom_avatars': ('avatar' in django_settings.INSTALLED_APPS),
        'tab_name' : 'stats',
        'tab_description' : _('user profile'),
        'page_title' : _('user profile overview'),
        'user_status_for_display': user.get_status_display(soft = True),
        'questions' : questions,
        'questions_count': question_count,

        'top_answers': top_answers,
        'top_answer_count': top_answer_count,

        'up_votes' : up_votes,
        'down_votes' : down_votes,
        'total_votes': up_votes + down_votes,
        'votes_today_left': votes_total - votes_today,
        'votes_total_per_day': votes_total,

        'user_tags' : user_tags,

        'badges': badges,
        'total_badges' : len(badges),
        'main_list': main_list,
        'sidebar_list': sidebar_list,
    }
    context.update(data)

    return render_into_skin('user_profile/user_stats_vip.html', context, request)

def user_recent(request, user, context):

    def get_type_name(type_id):
        for item in const.TYPE_ACTIVITY:
            if type_id in item:
                return item[1]

    class Event(object):
        is_badge = False
        def __init__(self, time, type, title, summary, answer_id, question_id):
            self.time = time
            self.type = get_type_name(type)
            self.type_id = type
            self.title = title
            self.summary = summary
            slug_title = slugify(title)
            self.title_link = reverse(
                                'question',
                                kwargs={'id':question_id}
                            ) + u'%s' % slug_title
            if int(answer_id) > 0:
                self.title_link += '#%s' % answer_id

    class AwardEvent(object):
        is_badge = True
        def __init__(self, time, type, content_object, badge):
            self.time = time
            self.type = get_type_name(type)
            self.content_object = content_object
            self.badge = badge

    activities = []

    # TODO: Don't process all activities here for the user, only a subset ([:const.USER_VIEW_DATA_SIZE])
    for activity in models.Activity.objects.filter(user=user):

        # TODO: multi-if means that we have here a construct for which a design pattern should be used

        # ask questions
        if activity.activity_type == const.TYPE_ACTIVITY_ASK_QUESTION:
            q = activity.content_object
            if q.deleted:
                activities.append(Event(
                    time=activity.active_at,
                    type=activity.activity_type,
                    title=q.thread.title,
                    summary='', #q.summary,  # TODO: was set to '' before, but that was probably wrong
                    answer_id=0,
                    question_id=q.id
                ))

        elif activity.activity_type == const.TYPE_ACTIVITY_ANSWER:
            ans = activity.content_object
            question = ans.thread._question_post()
            if not ans.deleted and not question.deleted:
                activities.append(Event(
                    time=activity.active_at,
                    type=activity.activity_type,
                    title=ans.thread.title,
                    summary=question.summary,
                    answer_id=ans.id,
                    question_id=question.id
                ))

        elif activity.activity_type == const.TYPE_ACTIVITY_COMMENT_QUESTION:
            cm = activity.content_object
            q = cm.parent
            assert q.is_question()
            if not q.deleted:
                activities.append(Event(
                    time=cm.added_at,
                    type=activity.activity_type,
                    title=q.thread.title,
                    summary='',
                    answer_id=0,
                    question_id=q.id
                ))

        elif activity.activity_type == const.TYPE_ACTIVITY_COMMENT_ANSWER:
            cm = activity.content_object
            ans = cm.parent
            assert ans.is_answer()
            question = ans.thread._question_post()
            if not ans.deleted and not question.deleted:
                activities.append(Event(
                    time=cm.added_at,
                    type=activity.activity_type,
                    title=ans.thread.title,
                    summary='',
                    answer_id=ans.id,
                    question_id=question.id
                ))

        elif activity.activity_type == const.TYPE_ACTIVITY_UPDATE_QUESTION:
            q = activity.content_object
            if not q.deleted:
                activities.append(Event(
                    time=activity.active_at,
                    type=activity.activity_type,
                    title=q.thread.title,
                    summary=q.summary,
                    answer_id=0,
                    question_id=q.id
                ))

        elif activity.activity_type == const.TYPE_ACTIVITY_UPDATE_ANSWER:
            ans = activity.content_object
            question = ans.thread._question_post()
            if not ans.deleted and not question.deleted:
                activities.append(Event(
                    time=activity.active_at,
                    type=activity.activity_type,
                    title=ans.thread.title,
                    summary=ans.summary,
                    answer_id=ans.id,
                    question_id=question.id
                ))

        elif activity.activity_type == const.TYPE_ACTIVITY_MARK_ANSWER:
            ans = activity.content_object
            question = ans.thread._question_post()
            if not ans.deleted and not question.deleted:
                activities.append(Event(
                    time=activity.active_at,
                    type=activity.activity_type,
                    title=ans.thread.title,
                    summary='',
                    answer_id=0,
                    question_id=question.id
                ))

        elif activity.activity_type == const.TYPE_ACTIVITY_PRIZE:
            award = activity.content_object
            activities.append(AwardEvent(
                time=award.awarded_at,
                type=activity.activity_type,
                content_object=award.content_object,
                badge=award.badge,
            ))

    activities.sort(key=operator.attrgetter('time'), reverse=True)

    data = {
        'active_tab': 'users',
        'page_class': 'user-profile-page',
        'tab_name' : 'recent',
        'tab_description' : _('recent user activity'),
        'page_title' : _('profile - recent activity'),
        'activities' : activities[:const.USER_VIEW_DATA_SIZE]
    }
    context.update(data)
    return render_into_skin('user_profile/user_recent.html', context, request)

@owner_or_moderator_required
def user_responses(request, user, context):
    """
    We list answers for question, comments, and
    answer accepted by others for this user.
    as well as mentions of the user

    user - the profile owner
    """

    section = 'forum'
    if request.user.is_moderator() or request.user.is_administrator():
        if 'section' in request.GET and request.GET['section'] == 'flags':
            section = 'flags'

    if section == 'forum':
        activity_types = const.RESPONSE_ACTIVITY_TYPES_FOR_DISPLAY
        activity_types += (const.TYPE_ACTIVITY_MENTION,)
    else:
        assert(section == 'flags')
        activity_types = (const.TYPE_ACTIVITY_MARK_OFFENSIVE,)

    memo_set = models.ActivityAuditStatus.objects.filter(
                    user = request.user,
                    activity__activity_type__in = activity_types
                ).select_related(
                    'activity',
                    'activity__content_type',
                    'activity__question__thread',
                    'activity__user',
                    'activity__user__gravatar',
                ).order_by(
                    '-activity__active_at'
                )[:const.USER_VIEW_DATA_SIZE]

    #todo: insert pagination code here

    response_list = list()
    for memo in memo_set:
        response = {
            'id': memo.id,
            'timestamp': memo.activity.active_at,
            'user': memo.activity.user,
            'is_new': memo.is_new(),
            'response_url': memo.activity.get_absolute_url(),
            'response_snippet': memo.activity.get_preview(),
            'response_title': memo.activity.question.thread.title,
            'response_type': memo.activity.get_activity_type_display(),
            'response_id': memo.activity.question.id,
            'nested_responses': [],
        }
        response_list.append(response)

    response_list.sort(lambda x,y: cmp(y['response_id'], x['response_id']))
    last_response_id = None #flag to know if the response id is different
    last_response_index = None #flag to know if the response index in the list is different
    filtered_response_list = list()

    for i, response in enumerate(response_list):
        #todo: agrupate users
        if response['response_id'] == last_response_id:
            original_response = dict.copy(filtered_response_list[len(filtered_response_list)-1])
            original_response['nested_responses'].append(response)
            filtered_response_list[len(filtered_response_list)-1] = original_response
        else:
            filtered_response_list.append(response)
            last_response_id = response['response_id']
            last_response_index = i

    response_list = filtered_response_list
    response_list.sort(lambda x,y: cmp(y['timestamp'], x['timestamp']))
    filtered_response_list = list()

    data = {
        'active_tab':'users',
        'page_class': 'user-profile-page',
        'tab_name' : 'inbox',
        'inbox_section':section,
        'tab_description' : _('comments and answers to others questions'),
        'page_title' : _('profile - responses'),
        'responses' : response_list,
    }
    context.update(data)
    return render_into_skin('user_profile/user_inbox.html', context, request)

def user_network(request, user, context):
    if 'followit' not in django_settings.INSTALLED_APPS:
        raise Http404
    data = {
        'tab_name': 'network',
        'tab_description' : _('followers and followed users'),
        'page_title' : _('profile - network'),
        'followed_users': user.get_followed_users(),
        'followers': user.get_followers(),
    }
    context.update(data)
    return render_into_skin('user_profile/user_network.html', context, request)

@owner_or_moderator_required
def user_votes(request, user, context):
    all_votes = list(models.Vote.objects.filter(user=user))
    votes = []
    for vote in all_votes:
        post = vote.voted_post
        if post.is_question():
            vote.title = post.thread.title
            vote.question_id = post.id
            vote.answer_id = 0
            votes.append(vote)
        elif post.is_answer():
            vote.title = post.thread.title
            vote.question_id = post.thread._question_post().id
            vote.answer_id = post.id
            votes.append(vote)

    votes.sort(key=operator.attrgetter('id'), reverse=True)

    data = {
        'active_tab':'users',
        'page_class': 'user-profile-page',
        'tab_name' : 'votes',
        'tab_description' : _('user vote record'),
        'page_title' : _('profile - votes'),
        'votes' : votes[:const.USER_VIEW_DATA_SIZE]
    }
    context.update(data)
    return render_into_skin('user_profile/user_votes.html', context, request)


def user_reputation(request, user, context):
    reputes = models.Repute.objects.filter(user=user).select_related('question', 'question__thread', 'user').order_by('-reputed_at')

    # prepare data for the graph - last values go in first
    rep_list = ['[%s,%s]' % (calendar.timegm(datetime.datetime.now().timetuple()) * 1000, user.reputation)]
    for rep in reputes:
        rep_list.append('[%s,%s]' % (calendar.timegm(rep.reputed_at.timetuple()) * 1000, rep.reputation))
    reps = ','.join(rep_list)
    reps = '[%s]' % reps

    data = {
        'active_tab':'users',
        'page_class': 'user-profile-page',
        'tab_name': 'reputation',
        'tab_description': _('user reputation in the community'),
        'page_title': _('profile - user reputation'),
        'reputation': reputes,
        'reps': reps
    }
    context.update(data)
    return render_into_skin('user_profile/user_reputation.html', context, request)

def user_transaction(request, user, context):
    amount = request.GET.get('amount')
    qid = request.GET.get('QID')
    confirmation = request.GET.get('confirmation')
    message=''
    title=''
    if request.method == 'POST':
        if 'query_trans' in request.POST:
            query_trans_form = forms.QueryTransactionForm(request.POST)
            if query_trans_form.is_valid():
                beginDate=query_trans_form.cleaned_data['beginDate'] 
                endDate=query_trans_form.cleaned_data['endDate'] 
            else:
                #message=query_trans_form.errors
                message=_('The Data you input have some errors. Please re-fill the data carefully')
                data = {
                    'active_tab':'users',
                    'page_class': 'user-profile-page',
                    'tab_name': 'transaction',
                    'tab_description': _('user balance'),
                    'page_title': _('profile - user balance'),
                    'transactions': None,
                    'query_trans_form': query_trans_form,
                    'trans': None,
                    'confirmation':confirmation,
                    'message':message,
                    'amount': amount,
                    'qid': qid,
                    'title': title,
                }
                context.update(data)
                return render_into_skin('user_profile/user_transaction.html', context, request)
        elif 'query_confirm' in request.POST:
            trans_confirm_form = forms.TransactionConfirmForm(request.POST)
            if trans_confirm_form.is_valid():
                confirmation = trans_confirm_form.cleaned_data['confirm_payment'] 
                if confirmation=='Y':
                    try:
                        amount = trans_confirm_form.cleaned_data['amount'] 
                        qid = trans_confirm_form.cleaned_data['qid']
                        user = request.user
                        question = Post.objects.filter(id=qid)[0]
                        comment = _('Paid')+unicode(amount)+_('Dollars')+_(' To puchase:')+question.get_question_title()
                        user.add_user_transaction(
                                        user = user,
                                        income =0,
                                        outcome =amount,
                                        transaction_type=forms.TYPE_TRANSACTION_PAID_FOR_CONTENT,
                                        comment = comment,
                                        timestamp = datetime.datetime.now(),
                                        QID=qid
                                    )
                        #re-direct to the question which user paid for   
                        #add the transaction to author
                        author = question.author
                        per_author = Decimal(askbot_settings.PERCENT_FOR_AUTHOR)
                        per_forum = Decimal(askbot_settings.PERCENT_FOR_FORUM)
                        receive = Decimal(amount) * per_author/100
                        toforum = Decimal(amount) * per_forum/100
                        comment = _('Receive')+unicode(receive)+_('Dollars')+_(' Puchase from:')+user.username
                        user.add_user_transaction(
                                        user = author,
                                        income =receive,
                                        outcome =0,
                                        transaction_type=forms.TYPE_TRANSACTION_RECEIVE_FROM_CONTENT,
                                        comment = comment,
                                        timestamp = datetime.datetime.now(),
                                        QID=qid
                                    )
                        #add transaction to admin
                        admin = models.User.objects.get(username = askbot_settings.NAME_OF_ADMINISTRATOR_USER)
                        comment = _('Receive')+unicode(toforum)+_('Dollars')+_(' Puchase from:')+user.username+_(' Author:')+author.username
                        user.add_user_transaction(
                                        user = admin,
                                        income =toforum,
                                        outcome =0,
                                        transaction_type=forms.TYPE_TRANSACTION_RECEIVE_FROM_CONTENT,
                                        comment = comment,
                                        timestamp = datetime.datetime.now(),
                                        QID=qid
                                    )
                    except:
                        request.user.message_set.create(message = unicode('Plesae set the forum company ID correct'))
                        return HttpResponseRedirect(reverse('index'))
                    return HttpResponseRedirect(question.get_absolute_url())
            else:
                #should not happen here
                message=trans_confirm_form.errors
                confirmation='Y'
    else:
        if confirmation=='Y':
            try:
                if int(amount)<0 or int(qid)<0:
                    message = 'The amount:'+unicode(amount)+' and qid:'+unicode(qid)
                title = Post.objects.filter(id=qid)[0].question.get_question_title()
            except:
                message = 'The amount:'+unicode(amount)+' and qid:'+unicode(qid)  
        endDate= datetime.date.today( )
        beginDate = (datetime.date.today( ) - datetime.timedelta(days=120))
        query_trans_form = forms.QueryTransactionForm()
    transactions = models.Transaction.objects.filter(user=user,trans_at__gte=beginDate-datetime.timedelta(days=1) ,trans_at__lte=endDate+datetime.timedelta(days=1) ).select_related('question', 'question__thread', 'user').order_by('-trans_at')

    # prepare data for the graph - last values go in first
    transaction_list = ['[%s,%s]' % (calendar.timegm(datetime.datetime.now().timetuple()) * 1000, user.balance)]
    for transaction in transactions:
        transaction_list.append('[%s,%s]' % (calendar.timegm(transaction.trans_at.timetuple()) * 1000, transaction.balance))
    trans = ','.join(transaction_list)
    trans = '[%s]' % trans

    if confirmation!='Y':
        confirmation=None
    # transactions for listview
    # trans for chart
    data = {
        'active_tab':'users',
        'page_class': 'user-profile-page',
        'tab_name': 'transaction',
        'tab_description': _('user balance'),
        'page_title': _('profile - user balance'),
        'transactions': transactions,
        'query_trans_form': query_trans_form,
        'trans': trans,
        'confirmation':confirmation,
        'message':message,
        'amount': amount,
        'qid': qid,
        'title': title,
    }
    context.update(data)
    return render_into_skin('user_profile/user_transaction.html', context, request)


def user_favorites(request, user, context):
    favorite_threads = user.user_favorite_questions.values_list('thread', flat=True)
    questions = models.Post.objects.filter(post_type='question', thread__in=favorite_threads)\
                    .select_related('thread', 'thread__last_activity_by')\
                    .order_by('-score', '-thread__last_activity_at')[:const.USER_VIEW_DATA_SIZE]

    data = {
        'active_tab':'users',
        'page_class': 'user-profile-page',
        'tab_name' : 'favorites',
        'tab_description' : _('users favorite questions'),
        'page_title' : _('profile - favorite questions'),
        'questions' : questions,
    }
    context.update(data)
    return render_into_skin('user_profile/user_favorites.html', context, request)


@owner_or_moderator_required
@csrf.csrf_protect
def user_email_subscriptions(request, user, context):

    logging.debug(get_request_info(request))
    if request.method == 'POST':
        email_feeds_form = forms.EditUserEmailFeedsForm(request.POST)
        tag_filter_form = forms.TagFilterSelectionForm(request.POST, instance=user)
        if email_feeds_form.is_valid() and tag_filter_form.is_valid():

            action_status = None
            tag_filter_saved = tag_filter_form.save()
            if tag_filter_saved:
                action_status = _('changes saved')
            if 'save' in request.POST:
                feeds_saved = email_feeds_form.save(user)
                if feeds_saved:
                    action_status = _('changes saved')
            elif 'stop_email' in request.POST:
                email_stopped = email_feeds_form.reset().save(user)
                initial_values = forms.EditUserEmailFeedsForm.NO_EMAIL_INITIAL
                email_feeds_form = forms.EditUserEmailFeedsForm(initial=initial_values)
                if email_stopped:
                    action_status = _('email updates canceled')
    else:
        #user may have been created by some app that does not know
        #about the email subscriptions, in that case the call below
        #will add any subscription settings that are missing
        #using the default frequencies
        user.add_missing_askbot_subscriptions()

        #initialize the form
        email_feeds_form = forms.EditUserEmailFeedsForm()
        email_feeds_form.set_initial_values(user)
        tag_filter_form = forms.TagFilterSelectionForm(instance=user)
        action_status = None

    data = {
        'active_tab': 'users',
        'page_class': 'user-profile-page',
        'tab_name': 'email_subscriptions',
        'tab_description': _('email subscription settings'),
        'page_title': _('profile - email subscriptions'),
        'email_feeds_form': email_feeds_form,
        'tag_filter_selection_form': tag_filter_form,
        'action_status': action_status,
    }
    context.update(data)
    return render_into_skin(
        'user_profile/user_email_subscriptions.html',
        context,
        request
    )

USER_VIEW_CALL_TABLE = {
    'vip': user_stats_vip,                    
    'stats': user_stats,
    'recent': user_recent,
    'inbox': user_responses,
    'network': user_network,
    'reputation': user_reputation,
    'transaction': user_transaction,
    'favorites': user_favorites,
    'votes': user_votes,
    'email_subscriptions': user_email_subscriptions,
    'moderation': user_moderate,
    'addtransaction': user_add_transaction,
    'layout': user_layout,
}
#todo: rename this function - variable named user is everywhere
def user(request, id, slug=None, tab_name=None):
    """Main user view function that works as a switchboard

    id - id of the profile owner

    todo: decide what to do with slug - it is not used
    in the code in any way
    """
    profile_owner = get_object_or_404(models.User, id = id)

    if not tab_name:
        tab_name = request.GET.get('sort', 'stats')

    user_view_func = USER_VIEW_CALL_TABLE.get(tab_name, user_stats)

    search_state = SearchState( # Non-default SearchState with user data set
        scope=None,
        sort=None,
        query=None,
        tags=None,
        author=profile_owner.id,
        page=None,
        user_logged_in=profile_owner.is_authenticated(),
    )

    context = {
        'view_user': profile_owner,
        'search_state': search_state,
        'user_follow_feature_on': ('followit' in django_settings.INSTALLED_APPS),
    }
    return user_view_func(request, profile_owner, context)

#todo: rename this function - variable named user is everywhere
def user_admin(request):
    """Show the infor of admin
    """
    try:
        profile_owner =  models.User.objects.get(username = askbot_settings.NAME_OF_ADMINISTRATOR_USER)
    except:
        profile_owner = get_object_or_404(models.User, id = 1)

    tab_name = request.GET.get('sort', 'stats')

    user_view_func = USER_VIEW_CALL_TABLE.get(tab_name, user_stats)

    search_state = SearchState( # Non-default SearchState with user data set
        scope=None,
        sort=None,
        query=None,
        tags=None,
        author=profile_owner.id,
        page=None,
        user_logged_in=profile_owner.is_authenticated(),
    )

    context = {
        'view_user': profile_owner,
        'search_state': search_state,
        'user_follow_feature_on': ('followit' in django_settings.INSTALLED_APPS),
    }
    return user_stats_vip(request, profile_owner, context)

@csrf.csrf_exempt
def update_has_custom_avatar(request):
    """updates current avatar type data for the user
    """
    if request.is_ajax() and request.user.is_authenticated():
        if request.user.avatar_type in ('n', 'g'):
            request.user.update_avatar_type()
            request.session['avatar_data_updated_at'] = datetime.datetime.now()
            return HttpResponse(simplejson.dumps({'status':'ok'}), mimetype='application/json')
    return HttpResponseForbidden()
