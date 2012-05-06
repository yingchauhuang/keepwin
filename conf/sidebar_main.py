﻿"""
Sidebar settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup
from askbot.deps.livesettings import values
from django.utils.translation import ugettext as _
from askbot.conf.super_groups import CONTENT_AND_UI

SIDEBAR_MAIN = ConfigurationGroup(
                    'SIDEBAR_MAIN',
                    _('Main page sidebar'),
                    super_group = CONTENT_AND_UI
                )

settings.register(
    values.LongStringValue(
        SIDEBAR_MAIN,
        'SIDEBAR_MAIN_HEADER',
        description = _('Custom sidebar header'),
        default = '',
        help_text = _(
                    'Use this area to enter content at the TOP of the sidebar'
                    'in HTML format.   When using this option '
                    '(as well as the sidebar footer), please '
                    'use the HTML validation service to make sure that '
                    'your input is valid and works well in all browsers.'
                    )
    )
)

settings.register(
    values.BooleanValue(
        SIDEBAR_MAIN,
        'SIDEBAR_SEARCH',
        description = _('Show Search block in sidebar'),
        help_text = _(
                    'Uncheck this if you want to hide the Search '
                    'block from the sidebar ' 
                    ),
        default = True
    )
)

settings.register(
    values.BooleanValue(
        SIDEBAR_MAIN,
        'SIDEBAR_PAYMENT',
        description = _('Show Payment block in sidebar'),
        help_text = _(
                    'Uncheck this if you want to hide the payment '
                    'block from the sidebar ' 
                    ),
        default = True
    )
)

settings.register(
    values.BooleanValue(
        SIDEBAR_MAIN,
        'SIDEBAR_MAIN_SHOW_AD',
        description = _('Show advertisement block in sidebar'),
        help_text = _(
                    'Uncheck this if you want to hide the advertisement '
                    'block from the sidebar ' 
                    ),
        default = True
    )
)

settings.register(
    values.LongStringValue(
        SIDEBAR_MAIN,
        'SIDEBAR_MAIN_AD_CONTENT',
        default = '',
        description = _('Custom portion of the HTML in SIDEBAR AD Bar'),
        help_text = _(
                    '<strong>To use this option</strong>, '
                    'check "Show advertisement block in SIDEBAR area;" '
                    'above. Contents of this box will be inserted '
                    'into the &lt;SIDEBAR__AD&gt; portion of the HTML '
                    'output.'
                    )
    )
)

settings.register(
    values.BooleanValue(
        SIDEBAR_MAIN,
        'SIDEBAR_MAIN_SHOW_AVATARS',
        description = _('Show avatar block in sidebar'),
        help_text = _(
                    'Uncheck this if you want to hide the avatar '
                    'block from the sidebar ' 
                    ),
        default = True
    )
)

settings.register(
    values.IntegerValue(
        SIDEBAR_MAIN,
        'SIDEBAR_MAIN_AVATAR_LIMIT',
        description = _('Limit how many avatars will be displayed on the sidebar'),
        default = 16 
    )
)


settings.register(
    values.BooleanValue(
        SIDEBAR_MAIN,
        'SIDEBAR_MAIN_SHOW_TAG_SELECTOR',
        description = _('Show tag selector in sidebar'),
        help_text = _(
                    'Uncheck this if you want to hide the options '
                    'for choosing interesting and ignored tags ' 
                    ),
        default = True
    )
)

settings.register(
    values.BooleanValue(
        SIDEBAR_MAIN,
        'SIDEBAR_MAIN_SHOW_TAGS',
        description = _('Show tag list/cloud in sidebar'),
        help_text = _(
                    'Uncheck this if you want to hide the tag '
                    'cloud or tag list from the sidebar ' 
                    ),
        default = True
    )
)

settings.register(
    values.LongStringValue(
        SIDEBAR_MAIN,
        'SIDEBAR_MAIN_FOOTER',
        description = _('Custom sidebar footer'),
        default = '',
        help_text = _(
                    'Use this area to enter content at the BOTTOM of the sidebar'
                    'in HTML format.   When using this option '
                    '(as well as the sidebar header), please '
                    'use the HTML validation service to make sure that '
                    'your input is valid and works well in all browsers.'
                    )
    )
)

