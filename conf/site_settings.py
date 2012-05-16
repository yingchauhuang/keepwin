"""
Q&A website settings - title, desctiption, basic urls
keywords
"""
from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import CONTENT_AND_UI
from askbot.deps import livesettings
from django.utils.translation import ugettext as _

QA_SITE_SETTINGS = livesettings.ConfigurationGroup(
                    'QA_SITE_SETTINGS',
                    _('URLS, keywords & greetings'),
                    super_group = CONTENT_AND_UI
                )

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_TITLE',
        default=_('Keepwin'),
        description=_('Site title for the Q&A forum')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_KEYWORDS',
        default=_('Keepwin,Stock,Investment,Taiwan Stock,CNPROG,forum,community'),
        description=_('Comma separated list of Q&A site keywords')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_COPYRIGHT',
        default=_('Keepwin copyright, 2012-2016.'),
        description=_('Copyright message to show in the footer')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_DESCRIPTION',
        default=_('Taiwan Stock Forum exchange investment'),
        description=_('Site description for the search engines')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_SHORT_NAME',
        default=_('Keepwin'),
        description=_('Short name for your Q&A forum')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_URL',
        default='http://www.keepwin.com.tw',
        description=_(
                'Base URL for your Q&A forum, must start with '
                'http or https'
            ),
    )
)

settings.register(
    livesettings.BooleanValue(
        QA_SITE_SETTINGS,
        'ENABLE_GREETING_FOR_ANON_USER',
        default = True,
        description = _('Check to enable greeting for anonymous user')
   )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'GREETING_FOR_ANONYMOUS_USER',
        default=_('Welcome you to Keepwin Forum !!!'),
        hidden=False,
        description=_(
                'Text shown in the greeting message '
                'shown to the anonymous user'
            ),
        help_text=_(
                'Use HTML to format the message '
            )
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'FEEDBACK_SITE_URL',
        description=_('Feedback site URL'),
        help_text=_(
                'If left empty, a simple internal feedback form '
                'will be used instead'
            )
    )
)
