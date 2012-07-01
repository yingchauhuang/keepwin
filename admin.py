# -*- coding: utf-8 -*-
"""
:synopsis: connector to standard Django admin interface

To make more models accessible in the Django admin interface, add more classes subclassing ``django.contrib.admin.Model``

Names of the classes must be like `SomeModelAdmin`, where `SomeModel` must 
exactly match name of the model used in the project
"""
from django.contrib import admin
from askbot import models

class AnonymousQuestionAdmin(admin.ModelAdmin):
    """AnonymousQuestion admin class"""

#class TagAdmin(admin.ModelAdmin):
#    """Tag admin class"""

#class VoteAdmin(admin.ModelAdmin):
#    """  admin class"""

#class FavoriteQuestionAdmin(admin.ModelAdmin):
#    """  admin class"""

class PostAdmin(admin.ModelAdmin):
    """  admin class"""
    list_display = ('thread','author','post_type','text','locked','last_edited_at')
    date_hierarchy = 'last_edited_at'
    list_filter = ('author',)
    
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
    list_filter = ('user',)

class UserInforAdmin(admin.ModelAdmin):
    """  admin class"""
    #list_filter = ['trans_at']
    list_display = ('user','gender','education','income','occupational','template','mobile','mobile_verified','address')
    list_filter = ('user',)
    
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