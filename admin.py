# -*- coding: utf-8 -*-
"""
:synopsis: connector to standard Django admin interface

To make more models accessible in the Django admin interface, add more classes subclassing ``django.contrib.admin.Model``

Names of the classes must be like `SomeModelAdmin`, where `SomeModel` must 
exactly match name of the model used in the project
"""
from django.contrib import admin
from askbot import models
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect

class AnonymousQuestionAdmin(admin.ModelAdmin):
    """AnonymousQuestion admin class"""

#class TagAdmin(admin.ModelAdmin):
#    """Tag admin class"""

#class VoteAdmin(admin.ModelAdmin):
#    """  admin class"""

#class FavoriteQuestionAdmin(admin.ModelAdmin):
#    """  admin class"""
def mark_deleted(modeladmin, request, queryset):
    queryset.update(deleted=true)
mark_deleted.short_description = _('Mark selected post as deleted')

class PostAdmin(admin.ModelAdmin):
    """  admin class"""
    list_display = ('author','post_type','thread','locked','last_edited_at')
    date_hierarchy = 'last_edited_at'
    search_fields  = ('author__username','text')
    actions = [mark_deleted]

class PostRevisionAdmin(admin.ModelAdmin):
    """  admin class"""

#class AwardAdmin(admin.ModelAdmin):
#    """  admin class"""

#class ReputeAdmin(admin.ModelAdmin):
#    """  admin class"""

#class ActivityAdmin(admin.ModelAdmin):
#    """  admin class"""
    
class TransactionAdmin(admin.ModelAdmin):
    """  admin class"""
    #list_filter = ['trans_at']
    list_display = ('question','user', 'trans_at', 'transaction_type','income','outcome','balance','comment')
    date_hierarchy = 'trans_at'
    search_fields  = ('user__username','question__text')
    actions = None
class UserInforAdmin(admin.ModelAdmin):
    """  admin class"""
    #list_filter = ['trans_at']
    list_display = ('user','gender','education','income','occupational','template','mobile','mobile_verified','address')
    search_fields  = ('user__username',)
    actions = None
class RSSAdmin(admin.ModelAdmin):
    """  admin RSS class"""
    #list_filter = ['trans_at']
    list_display = ('title','description','tagnames','imported')
    search_fields  = ('title','description')
    actions = None

def fetch_article(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    ct = ContentType.objects.get_for_model(queryset.model)
    return HttpResponseRedirect("/export/?ct=%s&ids=%s" % (ct.pk, ",".join(selected)))
fetch_article.short_description = _('Fetch Article')

class RSSSourceAdmin(admin.ModelAdmin):
    """  admin RSS class"""
    #list_filter = ['trans_at']
    list_display = ('name','link','coding','fetchtime')
    list_filter = ['name']
    actions = [fetch_article]

admin.site.disable_action('delete_selected')    
admin.site.register(models.Post, PostAdmin)
#admin.site.register(models.Tag, TagAdmin)
#admin.site.register(models.Vote, VoteAdmin)
#admin.site.register(models.FavoriteQuestion, FavoriteQuestionAdmin)
admin.site.register(models.PostRevision, PostRevisionAdmin)
#admin.site.register(models.Award, AwardAdmin)
#admin.site.register(models.Repute, ReputeAdmin)
#admin.site.register(models.Activity, ActivityAdmin)
admin.site.register(models.Transaction, TransactionAdmin)
admin.site.register(models.UserInfo, UserInforAdmin)
admin.site.register(models.RSS, RSSAdmin)
admin.site.register(models.RSSSource, RSSSourceAdmin)