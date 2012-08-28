"""
Social sharing settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import EXTERNAL_SERVICES
from askbot.deps.livesettings import ConfigurationGroup, BooleanValue
from django.utils.translation import ugettext as _

EXTERNAL_MODULES = ConfigurationGroup(
            'EXTERNAL_MODULES',
            _('The External Modules add by YC'), 
            super_group = EXTERNAL_SERVICES
        )

settings.register(
    BooleanValue(
        EXTERNAL_MODULES,
        'ENABLE_RSS_IMPORT',
        default=True,
        description=_('Check to enable RSS import module')
    )
)