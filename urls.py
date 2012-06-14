"""
askbot askbot url configuraion file
"""
import os.path
from django.conf import settings
from django.conf.urls.defaults import url, patterns, include
from django.conf.urls.defaults import handler500, handler404
from django.contrib import admin
from askbot import views
from askbot.feed import RssLastestQuestionsFeed, RssIndividualQuestionFeed
from askbot.sitemap import QuestionsSitemap
from askbot.skins.utils import update_media_revision

admin.autodiscover()
update_media_revision()#needs to be run once, so put it here

if getattr(settings, "ASKBOT_TRANSLATE_URL", False):
    from django.utils.translation import ugettext as _
else:
    _ = lambda s:s

feeds = {
    'rss': RssLastestQuestionsFeed,
    'question':RssIndividualQuestionFeed
}
sitemaps = {
    'questions': QuestionsSitemap
}

APP_PATH = os.path.dirname(__file__)
urlpatterns = patterns('',
    url(r'^$', views.readers.index, name='index'),
    url(
        r'^sitemap.xml$', 
        'django.contrib.sitemaps.views.sitemap', 
        {'sitemaps': sitemaps}, 
        name='sitemap'
    ),
    #no translation for this url!!
    url(r'import-data/$', views.writers.import_data, name='import_data'),
    url(r'^%s$' % _('about/'), views.meta.about, name='about'),
    url(r'^%s$' % _('faq/'), views.meta.faq, name='faq'),
    url(r'^%s$' % _('privacy/'), views.meta.privacy, name='privacy'),
    url(r'^%s$' % _('help/'), views.meta.help, name='help'),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('edit/')), 
        views.writers.edit_answer, 
        name='edit_answer'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('revisions/')), 
        views.readers.revisions, 
        kwargs = {'object_name': 'Answer'},
        name='answer_revisions'
    ),
    # The main page for keepwin                   
    url(
        # Note that all parameters, even if optional, are provided to the view. Non-present ones have None value.
        (r'^%s' % _('mainpage') +
            r'(%s)?' % r'/scope:(?P<scope>\w+)' +
            r'(%s)?' % r'/sort:(?P<sort>[\w\-]+)' +
            r'(%s)?' % r'/query:(?P<query>[^/]+)' +  # INFO: question string cannot contain slash (/), which is a section terminator
            r'(%s)?' % r'/tags:(?P<tags>[\w+.#,-]+)' + # Should match: const.TAG_CHARS + ','; TODO: Is `#` char decoded by the time URLs are processed ??
            r'(%s)?' % r'/author:(?P<author>\d+)' +
            r'(%s)?' % r'/page:(?P<page>\d+)' +
        r'/$'),
        views.readers.mainpage, 
        name='mainpage'
    ),
    # BEGIN Questions (main page) urls. All this urls work both normally and through ajax

    url(
        # Note that all parameters, even if optional, are provided to the view. Non-present ones have None value.
        (r'^%s' % _('questions') +
            r'(%s)?' % r'/scope:(?P<scope>\w+)' +
            r'(%s)?' % r'/sort:(?P<sort>[\w\-]+)' +
            r'(%s)?' % r'/query:(?P<query>[^/]+)' +  # INFO: question string cannot contain slash (/), which is a section terminator
            r'(%s)?' % r'/tags:(?P<tags>[\w+.#,-]+)' + # Should match: const.TAG_CHARS + ','; TODO: Is `#` char decoded by the time URLs are processed ??
            r'(%s)?' % r'/author:(?P<author>\d+)' +
            r'(%s)?' % r'/page:(?P<page>\d+)' +
        r'/$'),

        views.readers.questions, 
        name='questions'
    ),
                       
     url(
        # Note that all parameters, even if optional, are provided to the view. Non-present ones have None value.
        (r'^%s' % _('questions_snapshot') +
            r'(%s)?' % r'/scope:(?P<scope>\w+)' +
            r'(%s)?' % r'/sort:(?P<sort>[\w\-]+)' +
            r'(%s)?' % r'/query:(?P<query>[^/]+)' +  # INFO: question string cannot contain slash (/), which is a section terminator
            r'(%s)?' % r'/tags:(?P<tags>[\w+.#,-]+)' + # Should match: const.TAG_CHARS + ','; TODO: Is `#` char decoded by the time URLs are processed ??
            r'(%s)?' % r'/author:(?P<author>\d+)' +
            r'(%s)?' % r'/page:(?P<page>\d+)' +
        r'/$'),

        views.readers.questions_snapshot, 
        name='questions_snapshot'
    ),
                       
    # END main page urls
    
    url(
        r'^api/get_questions/',
        views.commands.api_get_questions,
        name = 'api_get_questions'
    ),
    url(
        r'^%s%s$' % (_('payment/'), _('ad_model/')), 
        views.payment.ad_model, 
        name='ad_model'
    ),
    url(
        r'^%s%s$' % (_('payment/'), _('FB_Channel/')), 
        views.payment.FB_Channel, 
        name='FB_Channel'
    ),
    url(
        r'^%s%s$' % (_('payment/'), _('Roturl/')), 
        views.payment.Roturl, 
        name='Payment_Roturl'
    ),
    url(
        r'^%s%s$' % (_('payment/'), _('Roturltest/')), 
        views.payment.Roturltest, 
        name='Payment_Roturltest'
    ),  
    url(
        r'^%s%s$' % (_('payment/'), _('ibon/')), 
        views.payment.ibon, 
        name='Payment_ibon'
    ),       
    url(
        r'^%s(?P<amount>\d+)/%s$' % (_('payment/'), _('confirm/')), 
        views.payment.confirm, 
        name='Payment_confirm'
    ),                 
    url(
        r'^%s%s$' % (_('questions/'), _('ask/')), 
        views.writers.ask, 
        name='ask'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('edit/')), 
        views.writers.edit_question, 
        name='edit_question'
    ),
    url(#this url is both regular and ajax
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('retag/')), 
        views.writers.retag_question, 
        name='retag_question'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('close/')), 
        views.commands.close, 
        name='close'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('reopen/')), 
        views.commands.reopen, 
        name='reopen'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('answer/')), 
        views.writers.answer, 
        name='answer'
    ),
    url(#ajax only
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('vote/')), 
        views.commands.vote, 
        name='vote'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('revisions/')), 
        views.readers.revisions, 
        kwargs = {'object_name': 'Question'},
        name='question_revisions'
    ),
    url(
        r'^%s%s$' % (_('widgets/'), _('questions/')),
        views.readers.widget_questions, 
        name='widget_questions'
    ),
    url(#ajax only
        r'^comment/upvote/$',
        views.commands.upvote_comment,
        name = 'upvote_comment'
    ),
    url(#ajax only
        r'^post_comments/$',
        views.writers.post_comments, 
        name='post_comments'
    ),
    url(#ajax only
        r'^edit_comment/$',
        views.writers.edit_comment,
        name='edit_comment'
    ),
    url(#ajax only
        r'^comment/delete/$',
        views.writers.delete_comment, 
        name='delete_comment'
    ),
    url(#ajax only
        r'^comment/get_text/$',
        views.readers.get_comment, 
        name='get_comment'
    ),
    url(
        r'^%s$' % _('tags/'), 
        views.readers.tags, 
        name='tags'
    ),
    url(#ajax only
        r'^%s%s$' % ('mark-tag/', 'interesting/'),
        views.commands.mark_tag,
        kwargs={'reason':'good','action':'add'},
        name='mark_interesting_tag'
    ),
    url(#ajax only
        r'^%s%s$' % ('mark-tag/', 'ignored/'),
        views.commands.mark_tag,
        kwargs={'reason':'bad','action':'add'},
        name='mark_ignored_tag'
    ),
    url(#ajax only
        r'^unmark-tag/',
        views.commands.mark_tag,
        kwargs={'action':'remove'},
        name='unmark_tag'
    ),
    url(#ajax only
        r'^set-tag-filter-strategy/',
        views.commands.set_tag_filter_strategy,
        name = 'set_tag_filter_strategy'
    ),
    url(
        r'^get-tags-by-wildcard/',
        views.commands.get_tags_by_wildcard,
        name = 'get_tags_by_wildcard'
    ),
    url(
        r'^get-tag-list/',
        views.commands.get_tag_list,
        name = 'get_tag_list'
    ),
    url(
        r'^swap-question-with-answer/',
        views.commands.swap_question_with_answer,
        name = 'swap_question_with_answer'
    ),
    url(
        r'^%s$' % _('subscribe-for-tags/'),
        views.commands.subscribe_for_tags,
        name = 'subscribe_for_tags'
    ),
    url(
        r'^%s$' % _('users/'),
        views.users.users, 
        name='users'
    ),
    url(
        r'^%s$' % _('users_admin/'),
        views.users.users_admin, 
        name='users_admin'
    ),
    #todo: rename as user_edit, b/c that's how template is named
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('users/'), _('edit/')),
        views.users.edit_user,
        name='edit_user'
    ),
    url(
        r'^%s(?P<id>\d+)/(?P<slug>.+)/%s$' % (
            _('users/'),
            _('subscriptions/'),
        ),
        views.users.user,
        kwargs = {'tab_name': 'email_subscriptions'},
        name = 'user_subscriptions'
    ),
    url(
        r'^%s(?P<id>\d+)/(?P<slug>.+)/$' % _('users/'),
        views.users.user,
        name='user_profile'
    ),
    url(
        r'^%s$' % _('users/update_has_custom_avatar/'),
        views.users.update_has_custom_avatar,
        name='user_update_has_custom_avatar'
    ),
    url(
        r'^%s$' % _('badges/'),
        views.meta.badges,
        name='badges'
    ),
    url(
        r'^%s(?P<id>\d+)//*' % _('badges/'),
        views.meta.badge,
        name='badge'
    ),
    url(#ajax only
        r'^%s%s$' % (_('messages/'), _('markread/')),
        views.commands.read_message,
        name='read_message'
    ),
    url(#ajax only
        r'^manage_inbox/$',
        views.commands.manage_inbox,
        name='manage_inbox'
    ),
    url(
        r'^feeds/(?P<url>.*)/$', 
        'django.contrib.syndication.views.feed',
        {'feed_dict': feeds},
        name='feeds'
    ),
	url(r'^%s$' % _('user_admin/'), views.users.user_admin, name='user_admin'),
    url(r'^%s$' % _('save_template/'), views.users.save_template, name='save_template'),
    url(r'^%s$' % _('add_template/'), views.users.add_template, name='add_template'), 
    url(r'^%s$' % _('del_template/'), views.users.delete_template, name='delete_template'), 
    url(r'^%s$' % _('update_template/'), views.users.update_template_content, name='update_template_content'), 
    #upload url is ajax only
    url( r'^%s$' % _('upload/'), views.writers.upload, name='upload'),
    url(r'^%s$' % _('feedback/'), views.meta.feedback, name='feedback'),
    #url(r'^feeds/rss/$', RssLastestQuestionsFeed, name="latest_questions_feed"),
    url(
        r'^doc/(?P<path>.*)$', 
        'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH,'doc','build','html').replace('\\','/')},
        name='askbot_docs',
    ),
    url(
        '^custom\.css$',
        views.meta.config_variable,
        kwargs = {
            'variable_name': 'CUSTOM_CSS',
            'mimetype': 'text/css'
        },
        name = 'custom_css'
    ),
    url(
        '^custom\.js$',
        views.meta.config_variable,
        kwargs = {
            'variable_name': 'CUSTOM_JS',
            'mimetype': 'text/javascript'
        },
        name = 'custom_js'
    ),
    url(
        r'^jsi18n/$',
        'django.views.i18n.javascript_catalog',
        {'domain': 'djangojs','packages': ('askbot',)},
        name = 'askbot_jsi18n'
    ),
)

if getattr(settings, 'ASKBOT_USE_STACKEXCHANGE_URLS', False):
    urlpatterns += (url(
        r'^%s(?P<id>\d+)/' % _('questions/'), 
        views.readers.question, 
        name='question'
    ),)
else:
    urlpatterns += (url(
        r'^%s(?P<id>\d+)/' % _('question/'), 
        views.readers.question, 
        name='question'
    ),)

if 'askbot.deps.django_authopenid' in settings.INSTALLED_APPS:
    urlpatterns += (
        url(r'^%s' % _('account/'), include('askbot.deps.django_authopenid.urls')),
    )

if 'avatar' in settings.INSTALLED_APPS:
    #unforturately we have to wire avatar urls here,
    #because views add and change are adapted to
    #use jinja2 templates
    urlpatterns += (
        url('^avatar/add/$', views.avatar_views.add, name='avatar_add'),
        url(
            '^avatar/change/$',
            views.avatar_views.change,
            name='avatar_change'
        ),
        url(
            '^avatar/delete/$',
            views.avatar_views.delete,
            name='avatar_delete'
        ),
        url(#this urs we inherit from the original avatar app
            '^avatar/render_primary/(?P<user_id>[\+\d]+)/(?P<size>[\d]+)/$',
            views.avatar_views.render_primary,
            name='avatar_render_primary'
        ),
    )
