"""
Social sharing settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import EXTERNAL_SERVICES
from askbot.deps.livesettings import ConfigurationGroup, BooleanValue
from django.utils.translation import ugettext as _

SOCIAL_SHARING = ConfigurationGroup(
            'SOCIAL_SHARING',
            _('Sharing content on social networks'), 
            super_group = EXTERNAL_SERVICES
        )

settings.register(
    BooleanValue(
        SOCIAL_SHARING,
        'ENABLE_SHARING_TWITTER',
        default=True,
        description=_('Check to enable sharing of questions on Twitter')
    )
)

settings.register(
    BooleanValue(
        SOCIAL_SHARING,
        'ENABLE_SHARING_FACEBOOK',
        default=True,
        description=_('Check to enable sharing of questions on Facebook')
    )
)

settings.register(
    BooleanValue(
        SOCIAL_SHARING,
        'ENABLE_SHARING_LINKEDIN',
        default=True,
        description=_('Check to enable sharing of questions on LinkedIn')
    )
)

settings.register(
    BooleanValue(
        SOCIAL_SHARING,
        'ENABLE_SHARING_IDENTICA',
        default=True,
        description=_('Check to enable sharing of questions on Identi.ca')
    )
)

settings.register(
    BooleanValue(
        SOCIAL_SHARING,
        'ENABLE_SHARING_GOOGLE',
        default=True,
        description=_('Check to enable sharing of questions on Google+')
    )
)

settings.register(
    BooleanValue(
        SOCIAL_SHARING,
        'ENABLE_FACEBOOK_DISCUSSION',
        default=True,
        description=_('Check to enable the facebook discussion area')
    )
)


settings.register(
    BooleanValue(
        SOCIAL_SHARING,
        'ENABLE_DISQUES_DISCUSSION',
        default=True,
        description=_('Check to enable the disques discussion area')
    )
)

settings.register(
    BooleanValue(
        SOCIAL_SHARING,
        'ENABLE_SHARING_LINK',
        default=True,
        description=_('Check to enable the social sharing post link')
    )
)
