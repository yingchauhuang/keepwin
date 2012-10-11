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
from askbot.models.transaction import Transaction
#from django.contrib.admin.filterspecs import FilterSpec, ChoicesFilterSpec,DateFieldFilterSpec
from django.db import connection
from CSV_Export import export_as_csv_action

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

class ThreadAdmin(admin.ModelAdmin):
    """  admin class"""
    list_display = ('title','tagnames','subtitle','OnTop')
    date_hierarchy = 'last_activity_at'
    search_fields  = ('title','subtitle')
    actions = [mark_deleted]
    fieldsets = (
        (None, {
            'fields': ('title','tagnames','subtitle','OnTop')
        }),
    )
        # Other stuff here
    def get_actions(self, request):
        actions = super(ThreadAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def has_delete_permission(self, request, obj=None):
        return False
    
class PostAdmin(admin.ModelAdmin):
    """  admin class"""
    list_display = ('author','post_type','thread','locked','last_edited_at')
    date_hierarchy = 'last_edited_at'
    search_fields  = ('author__username','text')
    actions = [mark_deleted]
        # Other stuff here
    def get_actions(self, request):
        actions = super(PostAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def has_delete_permission(self, request, obj=None):
        return False
    
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
    list_filter = ('transaction_type',)
    search_fields  = ('user__username','question__text')
    actions = [export_as_csv_action("CSV Export")]
    
class TransactionCheckAdmin(admin.ModelAdmin):
    """  admin class"""
    #list_filter = ['trans_at']
    list_display = ('question','user', 'trans_at', 'transaction_type','income','outcome','balance','comment')
    #date_hierarchy = 'trans_at'
    def queryset(self, request):
        qs = super(TransactionCheckAdmin, self).queryset(request)
        cursor = connection.cursor()
        cursor.execute("select refer_id from (select refer_id,sum(outcome) as outcome,sum(income) as income from transaction where transaction_type in (20,10) and issettled!=True group by refer_id) as t where t.income!=t.outcome and refer_id is not null;")
        unbalance_question = list()
        unbalance_question_result = cursor.fetchall()
        for row in unbalance_question_result:
            unbalance_question.append(row[0])
        return qs.filter(refer__in=unbalance_question)
    #search_fields  = ('user__username','question__text')
    #actions = None
    
class UserInforAdmin(admin.ModelAdmin):
    """  admin class"""
    #list_filter = ['trans_at']
    list_display = ('user','balance','gender','education','income','occupational','template','mobile','mobile_verified','address')
    search_fields  = ('user__username',)
    actions = None
    
#class UserBalanceAdmin(admin.ModelAdmin):
#    """  admin class"""
#    #list_filter = ['trans_at']
#    list_display = ('user', 'balance')
#    search_fields  = ('username',)
#    actions = None
    
class rssAdmin(admin.ModelAdmin):
    """  admin rss class"""
    #list_filter = ['trans_at']
    list_display = ('title','description','tagnames','imported')
    search_fields  = ('title','description')
    actions = None

def fetch_article(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    ct = ContentType.objects.get_for_model(queryset.model)
    return HttpResponseRedirect("/export/?ct=%s&ids=%s" % (ct.pk, ",".join(selected)))
fetch_article.short_description = _('Fetch Article')

class rsssourceAdmin(admin.ModelAdmin):
    """  admin rss class"""
    #list_filter = ['trans_at']
    list_display = ('name','link','coding','fetchtime')
    list_filter = ['name']
    actions = [fetch_article]

#admin.site.disable_action('delete_selected')  
admin.site.register(models.Thread, ThreadAdmin)  
admin.site.register(models.Post, PostAdmin)
#admin.site.register(models.Tag, TagAdmin)
#admin.site.register(models.Vote, VoteAdmin)
#admin.site.register(models.FavoriteQuestion, FavoriteQuestionAdmin)
admin.site.register(models.PostRevision, PostRevisionAdmin)
#admin.site.register(models.Award, AwardAdmin)
#admin.site.register(models.Repute, ReputeAdmin)
#admin.site.register(models.Activity, ActivityAdmin)
admin.site.register(models.Transaction, TransactionAdmin)
#admin.site.register(models.Transaction, TransactionCheckAdmin)
admin.site.register(models.UserInfo, UserInforAdmin)
#admin.site.register(models.User, UserBalanceAdmin)
admin.site.register(models.rss, rssAdmin)
admin.site.register(models.rsssource, rsssourceAdmin)