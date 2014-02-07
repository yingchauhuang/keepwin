from collections import defaultdict
import datetime
import operator
import cgi
import logging
import sys
# for handling feature pic
import os
import urllib
import lxml.html
import cStringIO
from PIL import Image
from django.utils.html import strip_tags
from django.contrib.sitemaps import ping_google
from django.utils import html
from django.conf import settings
from django.contrib.auth.models import User
from django.core import urlresolvers
from django.db import models
from django.utils import html as html_utils
from django.utils.translation import ugettext as _
from django.utils.http import urlquote as django_urlquote
from django.core import exceptions as django_exceptions
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
import askbot

from askbot.utils.slug import slugify
from askbot import const
from askbot.models.user import EmailFeedSetting
from askbot.models.transaction import Transaction
from askbot.models.tag import MarkedTag, tags_match_some_wildcard
from askbot.conf import settings as askbot_settings
from askbot import exceptions
from askbot.utils import markup
from askbot.utils.html import sanitize_html
from askbot.models.base import BaseQuerySetManager

#todo: maybe merge askbot.utils.markup and forum.utils.html
from askbot.utils.diff import textDiff as htmldiff
from askbot.utils import mysql
from django.core import cache
from askbot.skins.loaders import get_template

class PostQuerySet(models.query.QuerySet):
    """
    Custom query set subclass for :class:`~askbot.models.Post`
    """
    #todo: we may not need this query set class,
    #as all methods on this class seem to want to
    #belong to Thread manager or Query set.

    def get_by_text_query(self, search_query):
        """returns a query set of questions,
        matching the full text query
        """
        return self.filter(
            models.Q(thread__title__icontains = search_query)\
            | models.Q(text__icontains = search_query)\
            | models.Q(thread__tagnames = search_query)\
            | models.Q(thread__posts__text__icontains = search_query, thread__posts__post_type='answer')
        )
#        #todo - goes to thread - we search whole threads
#        if getattr(settings, 'USE_SPHINX_SEARCH', False):
#            matching_questions = Question.sphinx_search.query(search_query)
#            question_ids = [q.id for q in matching_questions]
#            return Question.objects.filter(deleted = False, id__in = question_ids)
#        if settings.DATABASE_ENGINE == 'mysql' and mysql.supports_full_text_search():
#            return self.filter(
#                models.Q(thread__title__search = search_query)\
#                | models.Q(text__search = search_query)\
#                | models.Q(thread__tagnames__search = search_query)\
#                | models.Q(answers__text__search = search_query)
#            )
#        elif 'postgresql_psycopg2' in askbot.get_database_engine_name():
#            rank_clause = "ts_rank(question.text_search_vector, plainto_tsquery(%s))";
#            search_query = '&'.join(search_query.split())
#            extra_params = (search_query,)
#            extra_kwargs = {
#                'select': {'relevance': rank_clause},
#                'where': ['text_search_vector @@ plainto_tsquery(%s)'],
#                'params': extra_params,
#                'select_params': extra_params,
#                }
#            return self.extra(**extra_kwargs)
#        else:
#            #fallback to dumb title match search
#            return self.filter(thread__title__icontains=search_query)

    def added_between(self, start, end):
        """questions added between ``start`` and ``end`` timestamps"""
        #todo: goes to thread
        return self.filter(
            added_at__gt = start
        ).exclude(
            added_at__gt = end
        )

    def get_questions_needing_reminder(self,
                                       user = None,
                                       activity_type = None,
                                       recurrence_delay = None):
        """returns list of questions that need a reminder,
        corresponding the given ``activity_type``
        ``user`` - is the user receiving the reminder
        ``recurrence_delay`` - interval between sending the
        reminders about the same question
        """
        #todo: goes to thread
        from askbot.models import Activity#avoid circular import
        question_list = list()
        for question in self:
            try:
                activity = Activity.objects.get(
                    user = user,
                    question = question,
                    activity_type = activity_type
                )
                now = datetime.datetime.now()
                if now < activity.active_at + recurrence_delay:
                    continue
            except Activity.DoesNotExist:
                activity = Activity(
                    user = user,
                    question = question,
                    activity_type = activity_type,
                    content_object = question,
                )
            activity.active_at = datetime.datetime.now()
            activity.save()
            question_list.append(question)
        return question_list

    def get_author_list(self, **kwargs):
        #todo: - this is duplication - answer manager also has this method
        #will be gone when models are consolidated
        #note that method get_question_and_answer_contributors is similar in function
        #todo: goes to thread
        authors = set()
        for question in self:
            authors.update(question.get_author_list(**kwargs))
        return list(authors)


class PostManager(BaseQuerySetManager):
    def get_query_set(self):
        return PostQuerySet(self.model)

    def get_questions(self):
        return self.filter(post_type='question')

    def get_answers(self):
        return self.filter(post_type='answer')

    def get_comments(self):
        return self.filter(post_type='comment')

    def create_new_answer(self, thread, author, added_at, text, wiki=False, email_notify=False, is_private=False):
        # TODO: Some of this code will go to Post.objects.create_new
        answer = Post(
            post_type='answer',
            thread=thread,
            author=author,
            added_at=added_at,
            wiki=wiki,
            text=text,
            is_private=is_private,
            #.html field is denormalized by the save() call
        )
        if answer.wiki:
            answer.last_edited_by = answer.author
            answer.last_edited_at = added_at
            answer.wikified_at = added_at

        answer.parse_and_save(author=author)

        answer.add_revision(
            author=author,
            revised_at=added_at,
            text=text,
            comment = const.POST_STATUS['default_version'],
        )

        #update thread data
        thread.answer_count +=1
        thread.save()
        thread.set_last_activity(last_activity_at=added_at, last_activity_by=author) # this should be here because it regenerates cached thread summary html

        #set notification/delete
        if email_notify:
            thread.followed_by.add(author)
        else:
            thread.followed_by.remove(author)

        return answer

    def precache_comments(self, for_posts, visitor):
        """
        Fetches comments for given posts, and stores them in post._cached_comments
        Additionally, annotates posts with ``upvoted_by_user`` parameter, if visitor is logged in

        """
        qs = Post.objects.get_comments().filter(parent__in=for_posts).select_related('author')

        if visitor.is_anonymous():
            comments = list(qs.order_by('added_at'))
        else:
            upvoted_by_user = list(qs.filter(votes__user=visitor).distinct())
            not_upvoted_by_user = list(qs.exclude(votes__user=visitor).distinct())

            for c in upvoted_by_user:
                c.upvoted_by_user = 1  # numeric value to maintain compatibility with previous version of this code

            comments = upvoted_by_user + not_upvoted_by_user
            comments.sort(key=operator.attrgetter('added_at'))

        post_map = defaultdict(list)
        for cm in comments:
            post_map[cm.parent_id].append(cm)
        for post in for_posts:
            post._cached_comments = post_map[post.id]

        # Old Post.get_comment(self, visitor=None) method:
        #        if visitor.is_anonymous():
        #            return self.comments.order_by('added_at')
        #        else:
        #            upvoted_by_user = list(self.comments.filter(votes__user=visitor).distinct())
        #            not_upvoted_by_user = list(self.comments.exclude(votes__user=visitor).distinct())
        #
        #            for c in upvoted_by_user:
        #                c.upvoted_by_user = 1  # numeric value to maintain compatibility with previous version of this code
        #
        #            comments = upvoted_by_user + not_upvoted_by_user
        #            comments.sort(key=operator.attrgetter('added_at'))
        #
        #            return comments



class Post(models.Model):
    post_type = models.CharField(max_length=255, db_index=True)

    old_question_id = models.PositiveIntegerField(null=True, blank=True, default=None, unique=True)
    old_answer_id = models.PositiveIntegerField(null=True, blank=True, default=None, unique=True)
    old_comment_id = models.PositiveIntegerField(null=True, blank=True, default=None, unique=True)

    parent = models.ForeignKey('Post', blank=True, null=True, related_name='comments') # Answer or Question for Comment
    thread = models.ForeignKey('Thread', related_name='posts')

    author = models.ForeignKey(User, related_name='posts')
    added_at = models.DateTimeField(default=datetime.datetime.now)

    deleted     = models.BooleanField(default=False, db_index=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    deleted_by  = models.ForeignKey(User, null=True, blank=True, related_name='deleted_posts')

    wiki = models.BooleanField(default=False)
    wikified_at = models.DateTimeField(null=True, blank=True)

    locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(User, null=True, blank=True, related_name='locked_posts')
    locked_at = models.DateTimeField(null=True, blank=True)

    score = models.IntegerField(default=0)
    vote_up_count = models.IntegerField(default=0)
    vote_down_count = models.IntegerField(default=0)
    
    comment_count = models.PositiveIntegerField(default=0)
    offensive_flag_count = models.SmallIntegerField(default=0)

    last_edited_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(User, null=True, blank=True, related_name='last_edited_posts')
    
    featurepic = models.TextField(null=True)

    html = models.TextField(null=True)#html rendition of the latest revision
    text = models.TextField(null=True)#denormalized copy of latest revision

    # Denormalised data
    summary = models.CharField(max_length=180)

    #note: anonymity here applies to question only, but
    #the field will still go to thread
    #maybe we should rename it to is_question_anonymous
    #we might have to duplicate the is_anonymous on the Post,
    #if we are to allow anonymous answers
    #the reason is that the title and tags belong to thread,
    #but the question body to Post
    is_anonymous = models.BooleanField(default=False)
    
    #implemented by YC
    is_private = models.BooleanField(default=False)    #implemented for private answer
    is_charged = models.BooleanField(default=False)    #implemented for charged content
    cost = models.PositiveIntegerField(default=0)
    objects = PostManager()

    class Meta:
        app_label = 'askbot'
        db_table = 'askbot_post'
        verbose_name = _('Post')
        verbose_name_plural = _('Post')


    def get_absolute_url_yc(self):
        return  'http://%s%s' % (Site.objects.get_current().domain,self.get_absolute_url())
    
    def parse_post_text(post):
        """typically post has a field to store raw source text
        in comment it is called .comment, in Question and Answer it is
        called .text
        also there is another field called .html (consistent across models)
        so the goal of this function is to render raw text into .html
        and extract any metadata given stored in source (currently
        this metadata is limited by twitter style @mentions
        but there may be more in the future

        function returns a dictionary with the following keys
        html
        newly_mentioned_users - list of <User> objects
        removed_mentions - list of mention <Activity> objects - for removed ones
        """

        if post.is_answer() or post.is_question():
            _urlize = False
            _use_markdown = True
            _escape_html = False #markdow does the escaping
        elif post.is_comment():
            _urlize = True
            _use_markdown = True
            _escape_html = True
        else:
            raise NotImplementedError

        text = post.text

        if _escape_html:
            text = cgi.escape(text)

        if _urlize:
            text = html.urlize(text)

        if _use_markdown:
            text = sanitize_html(markup.get_parser().convert(text))

        #todo, add markdown parser call conditional on
        #post.use_markdown flag
        post_html = text
        mentioned_authors = list()
        removed_mentions = list()
        if '@' in text:
            op = post.get_origin_post()
            anticipated_authors = op.get_author_list(
                include_comments = True,
                recursive = True
            )

            extra_name_seeds = markup.extract_mentioned_name_seeds(text)

            extra_authors = set()
            for name_seed in extra_name_seeds:
                extra_authors.update(User.objects.filter(
                    username__istartswith = name_seed
                )
                )

            #it is important to preserve order here so that authors of post
            #get mentioned first
            anticipated_authors += list(extra_authors)

            mentioned_authors, post_html = markup.mentionize_text(
                text,
                anticipated_authors
            )

            #find mentions that were removed and identify any previously
            #entered mentions so that we can send alerts on only new ones
            from askbot.models.user import Activity
            if post.pk is not None:
                #only look for previous mentions if post was already saved before
                prev_mention_qs = Activity.objects.get_mentions(
                    mentioned_in = post
                )
                new_set = set(mentioned_authors)
                for prev_mention in prev_mention_qs:

                    user = prev_mention.get_mentioned_user()
                    if user is None:
                        continue
                    if user in new_set:
                        #don't report mention twice
                        new_set.remove(user)
                    else:
                        removed_mentions.append(prev_mention)
                mentioned_authors = list(new_set)

        data = {
            'html': post_html,
            'newly_mentioned_users': mentioned_authors,
            'removed_mentions': removed_mentions,
            }
        return data

    def _check_and_reset_featurepic(self,featurepic):
        
        if featurepic!=None:
            try:
                if featurepic.startswith(settings.MEDIA_URL):
                    checkfile= featurepic.replace(settings.MEDIA_URL, settings.MEDIA_ROOT)
                    if (os.path.exists(checkfile)):
                       return featurepic
                tree = lxml.html.document_fromstring(featurepic)
                images = tree.xpath("//img/@src")
                for image in images:
                    try:
                        if image.startswith(settings.MEDIA_URL):
                            checkfile= image.replace(settings.MEDIA_URL, settings.MEDIA_ROOT)
                            if (os.path.exists(checkfile)):
                                return image
                        code = urllib.urlopen(image).getcode()
                        if code != 404:
                            file=urllib.urlopen(image)
                            im = cStringIO.StringIO(file.read())
                            img=Image.open(im)
                            img.convert('RGB').save(settings.MEDIA_ROOT+unicode(self.id)+".jpg")
                            return settings.MEDIA_URL+unicode(self.id)+".jpg" 
                    except IOError:
                        urllib.urlretrieve(image, settings.MEDIA_ROOT+unicode(self.id))
                        img=Image.open(settings.MEDIA_ROOT+unicode(self.id))
                        img.convert('RGB').save(settings.MEDIA_ROOT+unicode(self.id)+".jpg")
                        return settings.MEDIA_URL+unicode(self.id)+".jpg" 
                    except Exception, e:
                        message = stre(e)
                        pass
            except :
                return None
        return None
#    def upload_featurepic_to_local(self,featurepic,id):
#        """
#        upload the image link file to local 
#        and conver the orginal link to local link
#        """
#
#        if featurepic!=None:
#            try:
#                tree = lxml.html.document_fromstring(featurepic)
#                images = tree.xpath("//img/@src")
#                for image in images:
#                    try:
#                        if image.startswith(settings.MEDIA_URL):
#                            checkfile= image.replace(settings.MEDIA_URL, settings.MEDIA_ROOT)
#                            if (os.path.exists(checkfile)):
#                                return image
#                        code = urllib.urlopen(image).getcode()
#                        if code != 404:
#                            file=urllib.urlopen(image)
#                            im = cStringIO.StringIO(file.read())
#                            img=Image.open(im)
#                            img.save(settings.MEDIA_ROOT+unicode(id)+".jpg")
#                            return settings.MEDIA_URL+unicode(id)+".jpg" 
#                    except :
#                        continue
#            except :
#                return user_get_avatar_url(self, size)
#        return user_get_avatar_url(self, size)
        
    #todo: when models are merged, it would be great to remove author parameter
    def parse_and_save_post(post, author = None, **kwargs):
        """generic method to use with posts to be used prior to saving
        post edit or addition
        """

        assert(author is not None)

        last_revision = post.html
        data = post.parse()

        post.html = data['html']
        newly_mentioned_users = set(data['newly_mentioned_users']) - set([author])
        removed_mentions = data['removed_mentions']

        #a hack allowing to save denormalized .summary field for questions
        if hasattr(post, 'summary'):
            post.summary = strip_tags(post.html)[:180]

        #delete removed mentions
        for rm in removed_mentions:
            rm.delete()

        created = post.pk is None

        #this save must precede saving the mention activity
        #because generic relation needs primary key of the related object
        super(post.__class__, post).save(**kwargs)
        post.featurepic=post._check_and_reset_featurepic(post.featurepic)
        super(post.__class__, post).save(**kwargs)
        if last_revision:
            diff = htmldiff(last_revision, post.html)
        else:
            diff = post.get_snippet()

        timestamp = post.get_time_of_last_edit()

        #todo: this is handled in signal because models for posts
        #are too spread out
        #remove by YC for performance 2012/06/01
        #from askbot.models import signals
        #signals.post_updated.send(
        #    post = post,
        #    updated_by = author,
        #    newly_mentioned_users = newly_mentioned_users,
        #    timestamp = timestamp,
        #    created = created,
        #    diff = diff,
        #    sender = post.__class__
        #)

        # for google SEO close by YC
        #try:
        #    from askbot.conf import settings as askbot_settings
        #    if askbot_settings.GOOGLE_SITEMAP_CODE != '':
        #        ping_google()
        #except Exception:
        #    logging.debug('cannot ping google - did you register with them?')

    ######################################
    # TODO: Rename the methods above instead of doing this assignment
    parse = parse_post_text
    parse_and_save = parse_and_save_post
    ######################################


    def is_question(self):
        return self.post_type == 'question'

    def is_answer(self):
        return self.post_type == 'answer'

    def is_comment(self):
        return self.post_type == 'comment'

    def get_absolute_url(self, no_slug = False, question_post=None, thread=None):
        from askbot.utils.slug import slugify
        if not hasattr(self, '_thread_cache') and thread:
            self._thread_cache = thread
        if self.is_answer():
            if not question_post:
                question_post = self.thread._question_post()
            return u'%(base)s%(slug)s?answer=%(id)d' % {
                'base': urlresolvers.reverse('question', args=[question_post.id]),
                'slug': django_urlquote(slugify(self.thread.title)),
                'id': self.id
            }
            '''
				return u'%(base)s%(slug)s?answer=%(id)d#answer-container-%(id)d' % {
                'base': urlresolvers.reverse('question', args=[question_post.id]),
                'slug': django_urlquote(slugify(self.thread.title)),
                'id': self.id
            '''
        elif self.is_question():
            url = urlresolvers.reverse('question', args=[self.id])
            if no_slug is False:
                url += django_urlquote(self.slug)
            return url
        elif self.is_comment():
            origin_post = self.get_origin_post()
            return '%(url)s?comment=%(id)d#comment-%(id)d' % \
                {'url': origin_post.get_absolute_url(), 'id':self.id}

        raise NotImplementedError

    def delete(self, **kwargs):
        """deletes comment and concomitant response activity
        records, as well as mention records, while preserving
        integrity or response counts for the users
        """
        if self.is_comment():
            #todo: implement a custom delete method on these
            #all this should pack into Activity.responses.filter( somehow ).delete()
            activity_types = const.RESPONSE_ACTIVITY_TYPES_FOR_DISPLAY
            activity_types += (const.TYPE_ACTIVITY_MENTION,)
            #todo: not very good import in models of other models
            #todo: potentially a circular import
            from askbot.models.user import Activity
            comment_content_type = ContentType.objects.get_for_model(self)
            activities = Activity.objects.filter(
                                content_type = comment_content_type,
                                object_id = self.id,
                                activity_type__in = activity_types
                            )

            recipients = set()
            for activity in activities:
                for user in activity.recipients.all():
                    recipients.add(user)

            #activities need to be deleted before the response
            #counts are updated
            activities.delete()

            for user in recipients:
                user.update_response_counts()

        super(Post, self).delete(**kwargs)

    def __unicode__(self):
        if self.is_question():
            return self.thread.title
        elif self.is_answer():
            return self.html
        elif self.is_comment():
            return self.text
        raise NotImplementedError

    def save(self, *args, **kwargs):
        if self.is_answer() and self.is_anonymous:
            raise ValueError('Answer cannot be anonymous!')
        super(Post, self).save(*args, **kwargs)
        if self.is_answer() and 'postgres' in askbot.get_database_engine_name():
            #hit the database to trigger update of full text search vector
            self.thread._question_post().save()

    def _get_slug(self):
        if not self.is_question():
            raise NotImplementedError
        return slugify(self.thread.title)
    slug = property(_get_slug)

    def get_snippet(self):
        """returns an abbreviated snippet of the content
        """
        return html_utils.strip_tags(self.html)[:120] + ' ...'

    def add_comment(self, comment=None, user=None, added_at=None):
        if added_at is None:
            added_at = datetime.datetime.now()
        if None in (comment ,user):
            raise Exception('arguments comment and user are required')

        from askbot.models import Post
        comment = Post(
            post_type='comment',
            thread=self.thread,
            parent=self,
            text=comment,
            author=user,
            added_at=added_at
        )
        comment.parse_and_save(author = user)
        self.comment_count = self.comment_count + 1
        self.save()

        #tried to add this to bump updated question
        #in most active list, but it did not work
        #becase delayed email updates would be triggered
        #for cases where user did not subscribe for them
        #
        #need to redo the delayed alert sender
        #
        #origin_post = self.get_origin_post()
        #if origin_post == self:
        #    self.last_activity_at = added_at # WARNING: last_activity_* are now in Thread
        #    self.last_activity_by = user
        #else:
        #    origin_post.last_activity_at = added_at
        #    origin_post.last_activity_by = user
        #    origin_post.save()

        return comment

    def get_global_tag_based_subscribers(
            self,
            tag_mark_reason = None,
            subscription_records = None
    ):
        """returns a list of users who either follow or "do not ignore"
        the given set of tags, depending on the tag_mark_reason

        ``subscription_records`` - query set of ``~askbot.models.EmailFeedSetting``
        this argument is used to reduce number of database queries
        """
        if tag_mark_reason == 'good':
            email_tag_filter_strategy = const.INCLUDE_INTERESTING
            user_set_getter = User.objects.filter
        elif tag_mark_reason == 'bad':
            email_tag_filter_strategy = const.EXCLUDE_IGNORED
            user_set_getter = User.objects.exclude
        else:
            raise ValueError('Uknown value of tag mark reason %s' % tag_mark_reason)

        #part 1 - find users who follow or not ignore the set of tags
        tag_names = self.get_tag_names()
        tag_selections = MarkedTag.objects.filter(
            tag__name__in = tag_names,
            reason = tag_mark_reason
        )
        subscribers = set(
            user_set_getter(
                tag_selections__in = tag_selections
            ).filter(
                notification_subscriptions__in = subscription_records
            ).filter(
                email_tag_filter_strategy = email_tag_filter_strategy
            )
        )

        #part 2 - find users who follow or not ignore tags via wildcard selections
        #inside there is a potentially time consuming loop
        if askbot_settings.USE_WILDCARD_TAGS:
            #todo: fix this
            #this branch will not scale well
            #because we have to loop through the list of users
            #in python
            if tag_mark_reason == 'good':
                empty_wildcard_filter = {'interesting_tags__exact': ''}
                wildcard_tags_attribute = 'interesting_tags'
                update_subscribers = lambda the_set, item: the_set.add(item)
            elif tag_mark_reason == 'bad':
                empty_wildcard_filter = {'ignored_tags__exact': ''}
                wildcard_tags_attribute = 'ignored_tags'
                update_subscribers = lambda the_set, item: the_set.discard(item)

            potential_wildcard_subscribers = User.objects.filter(
                notification_subscriptions__in = subscription_records
            ).filter(
                email_tag_filter_strategy = email_tag_filter_strategy
            ).exclude(
                **empty_wildcard_filter #need this to limit size of the loop
            )
            for potential_subscriber in potential_wildcard_subscribers:
                wildcard_tags = getattr(
                    potential_subscriber,
                    wildcard_tags_attribute
                ).split(' ')

                if tags_match_some_wildcard(tag_names, wildcard_tags):
                    update_subscribers(subscribers, potential_subscriber)

        return subscribers

    def get_global_instant_notification_subscribers(self):
        """returns a set of subscribers to post according to tag filters
        both - subscribers who ignore tags or who follow only
        specific tags

        this method in turn calls several more specialized
        subscriber retrieval functions
        todo: retrieval of wildcard tag followers ignorers
              won't scale at all
        """
        subscriber_set = set()

        global_subscriptions = EmailFeedSetting.objects.filter(
            feed_type = 'q_all',
            frequency = 'i'
        )

        #segment of users who have tag filter turned off
        global_subscribers = User.objects.filter(
            email_tag_filter_strategy = const.INCLUDE_ALL
        )
        subscriber_set.update(global_subscribers)

        #segment of users who want emails on selected questions only
        subscriber_set.update(
            self.get_global_tag_based_subscribers(
                subscription_records = global_subscriptions,
                tag_mark_reason = 'good'
            )
        )

        #segment of users who want to exclude ignored tags
        subscriber_set.update(
            self.get_global_tag_based_subscribers(
                subscription_records = global_subscriptions,
                tag_mark_reason = 'bad'
            )
        )
        return subscriber_set


    def _qa__get_instant_notification_subscribers(
            self,
            potential_subscribers = None,
            mentioned_users = None,
            exclude_list = None,
            ):
        """get list of users who have subscribed to
        receive instant notifications for a given post
        this method works for questions and answers

        Arguments:

        * ``potential_subscribers`` is not used here! todo: why? - clean this out
          parameter is left for the uniformity of the interface
          (Comment method does use it)
          normally these methods would determine the list
          :meth:`~askbot.models.question.Question.get_response_recipients`
          :meth:`~askbot.models.question.Answer.get_response_recipients`
          - depending on the type of the post
        * ``mentioned_users`` - users, mentioned in the post for the first time
        * ``exclude_list`` - users who must be excluded from the subscription

        Users who receive notifications are:

        * of ``mentioned_users`` - those who subscribe for the instant
          updates on the @name mentions
        * those who follow the parent question
        * global subscribers (any personalized tag filters are applied)
        * author of the question who subscribe to instant updates
          on questions that they asked
        * authors or any answers who subsribe to instant updates
          on the questions which they answered
        """
        #print '------------------'
        #print 'in content function'
        subscriber_set = set()
        #print 'potential subscribers: ', potential_subscribers

        #1) mention subscribers - common to questions and answers
        if mentioned_users:
            mention_subscribers = EmailFeedSetting.objects.filter_subscribers(
                potential_subscribers = mentioned_users,
                feed_type = 'm_and_c',
                frequency = 'i'
            )
            subscriber_set.update(mention_subscribers)

        origin_post = self.get_origin_post()

        #print origin_post

        #2) individually selected - make sure that users
        #are individual subscribers to this question
        # TODO: The line below works only if origin_post is Question !
        selective_subscribers = origin_post.thread.followed_by.all()
        #print 'question followers are ', [s for s in selective_subscribers]
        if selective_subscribers:
            selective_subscribers = EmailFeedSetting.objects.filter_subscribers(
                potential_subscribers = selective_subscribers,
                feed_type = 'q_sel',
                frequency = 'i'
            )
            subscriber_set.update(selective_subscribers)
            #print 'selective subscribers: ', selective_subscribers

        #3) whole forum subscribers
        global_subscribers = origin_post.get_global_instant_notification_subscribers()
        subscriber_set.update(global_subscribers)

        #4) question asked by me (todo: not "edited_by_me" ???)
        question_author = origin_post.author
        if EmailFeedSetting.objects.filter(subscriber = question_author, frequency = 'i', feed_type = 'q_ask').exists():
            subscriber_set.add(question_author)

        #4) questions answered by me -make sure is that people
        #are authors of the answers to this question
        #todo: replace this with a query set method
        answer_authors = set()
        for answer in origin_post.thread.posts.get_answers().all():
            authors = answer.get_author_list()
            answer_authors.update(authors)

        if answer_authors:
            answer_subscribers = EmailFeedSetting.objects.filter_subscribers(
                potential_subscribers = answer_authors,
                frequency = 'i',
                feed_type = 'q_ans',
            )
            subscriber_set.update(answer_subscribers)
            #print 'answer subscribers: ', answer_subscribers

        #print 'exclude_list is ', exclude_list
        subscriber_set -= set(exclude_list)

        #print 'final subscriber set is ', subscriber_set
        return list(subscriber_set)

    def _comment__get_instant_notification_subscribers(
                                    self,
                                    potential_subscribers = None,
                                    mentioned_users = None,
                                    exclude_list = None
                                ):
        """get list of users who want instant notifications about comments

        argument potential_subscribers is required as it saves on db hits

        Here is the list of people who will receive the notifications:

        * mentioned users
        * of response receivers
          (see :meth:`~askbot.models.meta.Comment.get_response_receivers`) -
          those who subscribe for the instant
          updates on comments and @mentions
        * all who follow the question explicitly
        * all global subscribers
          (tag filtered, and subject to personalized settings)
        """
        #print 'in meta function'
        #print 'potential subscribers: ', potential_subscribers

        subscriber_set = set()

        if potential_subscribers:
            potential_subscribers = set(potential_subscribers)
        else:
            potential_subscribers = set()

        if mentioned_users:
            potential_subscribers.update(mentioned_users)

        if potential_subscribers:
            comment_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                        potential_subscribers = potential_subscribers,
                                        feed_type = 'm_and_c',
                                        frequency = 'i'
                                    )
            subscriber_set.update(comment_subscribers)
            #print 'comment subscribers: ', comment_subscribers

        origin_post = self.get_origin_post()
        # TODO: The line below works only if origin_post is Question !
        selective_subscribers = origin_post.thread.followed_by.all()
        if selective_subscribers:
            selective_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                    potential_subscribers = selective_subscribers,
                                    feed_type = 'q_sel',
                                    frequency = 'i'
                                )
            for subscriber in selective_subscribers:
                if origin_post.passes_tag_filter_for_user(subscriber):
                    subscriber_set.add(subscriber)

            subscriber_set.update(selective_subscribers)
            #print 'selective subscribers: ', selective_subscribers

        global_subscribers = origin_post.get_global_instant_notification_subscribers()
        #print 'global subscribers: ', global_subscribers

        subscriber_set.update(global_subscribers)

        #print 'exclude list is: ', exclude_list
        if exclude_list:
            subscriber_set -= set(exclude_list)

        #print 'final list of subscribers:', subscriber_set

        return list(subscriber_set)

    def get_instant_notification_subscribers(self, potential_subscribers = None, mentioned_users = None, exclude_list = None):
        if self.is_question() or self.is_answer():
            return self._qa__get_instant_notification_subscribers(
                potential_subscribers=potential_subscribers,
                mentioned_users=mentioned_users,
                exclude_list=exclude_list
            )
        elif self.is_comment():
            return self._comment__get_instant_notification_subscribers(
                potential_subscribers=potential_subscribers,
                mentioned_users=mentioned_users,
                exclude_list=exclude_list
            )
        raise NotImplementedError

    def get_latest_revision(self):
        return self.revisions.order_by('-revised_at')[0]

    def get_latest_revision_number(self):
        if self.is_comment():
            return 1
        else:
            return self.get_latest_revision().revision

    def get_time_of_last_edit(self):
        if self.is_comment():
            return self.added_at

        if self.last_edited_at:
            return self.last_edited_at
        else:
            return self.added_at

    def get_owner(self): # TODO: remove me
        return self.author

    def get_author_list(
            self,
            include_comments = False,
            recursive = False,
            exclude_list = None):

        #todo: there may be a better way to do these queries
        authors = set()
        authors.update([r.author for r in self.revisions.all()])
        if include_comments:
            authors.update([c.author for c in self.comments.all()])
        if recursive:
            if self.is_question(): #hasattr(self, 'answers'):
                #for a in self.answers.exclude(deleted = True):
                for a in self.thread.posts.get_answers().exclude(deleted = True):
                    authors.update(a.get_author_list( include_comments = include_comments ) )
        if exclude_list:
            authors -= set(exclude_list)
        return list(authors)

    def passes_tag_filter_for_user(self, user):

        question = self.get_origin_post()
        if user.email_tag_filter_strategy == const.INCLUDE_INTERESTING:
            #at least some of the tags must be marked interesting
            return user.has_affinity_to_question(
                question,
                affinity_type = 'like'
            )
        elif user.email_tag_filter_strategy == const.EXCLUDE_IGNORED:
            return not user.has_affinity_to_question(
                question,
                affinity_type = 'dislike'
            )
        elif user.email_tag_filter_strategy == const.INCLUDE_ALL:
            return True
        else:
            raise ValueError(
                'unexpected User.email_tag_filter_strategy %s'\
                % user.email_tag_filter_strategy
            )

    def post_get_last_update_info(self):#todo: rename this subroutine
        when = self.added_at
        who = self.author
        if self.last_edited_at and self.last_edited_at > when:
            when = self.last_edited_at
            who = self.last_edited_by
        comments = self.comments.all()
        if len(comments) > 0:
            for c in comments:
                if c.added_at > when:
                    when = c.added_at
                    who = c.user
        return when, who

    def tagname_meta_generator(self):
        return u','.join([unicode(tag) for tag in self.get_tag_names()])

    def get_origin_post(self):
        if self.post_type == 'question':
            return self
        else:
            return self.thread._question_post()

    def _repost_as_question(self, new_title = None):
        """posts answer as question, together with all the comments
        while preserving time stamps and authors
        does not delete the answer itself though
        """
        if not self.is_answer():
            raise NotImplementedError
        revisions = self.revisions.all().order_by('revised_at')
        rev0 = revisions[0]
        new_question = rev0.author.post_question(
            title = new_title,
            body_text = rev0.text,
            tags = self.question.thread.tagnames,
            wiki = self.question.wiki,
            is_anonymous = self.question.is_anonymous,
            timestamp = rev0.revised_at
        )
        if len(revisions) > 1:
            for rev in revisions[1:]:
                rev.author.edit_question(
                    question = new_question,
                    body_text = rev.text,
                    revision_comment = rev.summary,
                    timestamp = rev.revised_at
                )
        for comment in self.comments.all():
            comment.content_object = new_question
            comment.save()
        return new_question

    def _repost_as_answer(self, question = None):
        """posts question as answer to another question,
        but does not delete the question,
        but moves all the comments to the new answer"""
        if not self.is_question():
            raise NotImplementedError
        revisions = self.revisions.all().order_by('revised_at')
        rev0 = revisions[0]
        new_answer = rev0.author.post_answer(
            question = question,
            body_text = rev0.text,
            wiki = self.wiki,
            timestamp = rev0.revised_at
        )
        if len(revisions) > 1:
            for rev in revisions:
                rev.author.edit_answer(
                    answer = new_answer,
                    body_text = rev.text,
                    revision_comment = rev.summary,
                    timestamp = rev.revised_at
                )
        for comment in self.comments.all():
            comment.content_object = new_answer
            comment.save()
        return new_answer

    def get_cached_summary_html(self):
        return cache.cache.get(self.SUMMARY_CACHE_KEY_TPL % self.id)
    
    def get_summary_html(self, search_state):
        html = self.get_cached_summary_html()
        if not html:
            html = self.update_summary_html()

        return html
    
    def update_summary_html(self):
        context = {
            'question': self._question_post(refresh=True),  # fetch new question post to make sure we're up-to-date
        }
        html = get_template('widgets/question_summary.html').render(context)
        # INFO: Timeout is set to 30 days:
        # * timeout=0/None is not a reliable cross-backend way to set infinite timeout
        # * We probably don't need to pollute the cache with threads older than 30 days
        # * Additionally, Memcached treats timeouts > 30day as dates (https://code.djangoproject.com/browser/django/tags/releases/1.3/django/core/cache/backends/memcached.py#L36),
        #   which probably doesn't break anything but if we can stick to 30 days then let's stick to it
        cache.cache.set(self.SUMMARY_CACHE_KEY_TPL % self.id, html, timeout=60*60*24*30)
        return html
    
    def swap_with_question(self, new_title = None):
        """swaps answer with the question it belongs to and
        sets the title of question to ``new_title``
        """
        if not self.is_answer():
            raise NotImplementedError
            #1) make new question by using new title, tags of old question
        #   and the answer body, as well as the authors of all revisions
        #   and repost all the comments
        new_question = self._repost_as_question(new_title = new_title)

        #2) post question (all revisions and comments) as answer
        new_answer = self.question._repost_as_answer(question = new_question)

        #3) assign all remaining answers to the new question
        self.question.answers.update(question = new_question)
        self.question.delete()
        self.delete()
        return new_question

    def get_featurePIC_url(self, size):
        """returns feature picture url 
        """
        if self.featurepic == None :
            return self.author.get_avatar_url(size) 
        else :
            return self.featurepic

    def get_user_vote(self, user):
        if not self.is_answer():
            raise NotImplementedError

        if user.is_anonymous():
            return None

        votes = self.votes.filter(user=user)
        if votes and votes.count() > 0:
            return votes[0]
        else:
            return None


    def _question__assert_is_visible_to(self, user):
        """raises QuestionHidden"""
        if self.deleted:
            message = _(
                'Sorry, this question has been '
                'deleted and is no longer accessible'
            )
            if user.is_anonymous():
                raise exceptions.QuestionHidden(message)
            try:
                user.assert_can_see_deleted_post(self)
            except django_exceptions.PermissionDenied:
                raise exceptions.QuestionHidden(message)
        if self.is_charged and self.author != user:
            """Check if user is anonymous """
            transaction = 0
            if user.id==None:   
                message = unicode('<BR>')+_('Sorry, you have to login first, then you can read it')+unicode('<BR>')+_(' <a href="/account/signin">login</a>')
            else:
                if user.balance>=self.cost:
                    """message = _('Sorry, you need to paid')+unicode(self.cost)+_(' first, then you can read it')+_(' <a href="{% url user_profile view_user.id, view_user.username|slugify %}?sort=transaction">I want to pay now</a>')"""
                    message = unicode('<BR>')+_('Sorry, you need to paid')+unicode(self.cost)+_(' first, then you can read it')+_(' Current Balance is ')+unicode(user.balance)+_('USD')+unicode('<BR>')+' <a href="/users/'+unicode(user.id)+'/'+unicode(user.username)+'?sort=transaction&amount='+unicode(self.cost)+'&QID='+unicode(self.id)+'&confirmation=Y'+'"'+_('>I want to pay now</a>')
                else:
                    message = unicode('<BR>')+_('Sorry, you need to paid')+unicode(self.cost)+_(' first, then you can read it')+unicode('<BR>')+_(' <a class="tag tag-msg" href="/payment/ibon/">I want to purchase credicts</a>')
                transaction=Transaction.objects.get_question_transaction(user,self)    
            if (transaction == 0):
                try:
                    if  (not user.is_administrator()):
                        raise exceptions.QuestionCharge(message)
                except:
                    raise exceptions.QuestionCharge(message)
    def _answer__assert_is_visible_to(self, user):
        """raises QuestionHidden or AnswerHidden"""
        try:
            self.thread._question_post().assert_is_visible_to(user)
        except exceptions.QuestionHidden:
            message = _(
                'Sorry, the answer you are looking for is '
                'no longer available, because the parent '
                'question has been removed'
            )
            raise exceptions.QuestionHidden(message)
        if self.deleted:
            message = _(
                'Sorry, this answer has been '
                'removed and is no longer accessible'
            )
            if user.is_anonymous():
                raise exceptions.AnswerHidden(message)
            try:
                user.assert_can_see_deleted_post(self)
            except django_exceptions.PermissionDenied:
                raise exceptions.AnswerHidden(message)

    def _comment__assert_is_visible_to(self, user):
        """raises QuestionHidden or AnswerHidden"""
        try:
            self.parent.assert_is_visible_to(user)
        except exceptions.QuestionHidden:
            message = _(
                        'Sorry, the comment you are looking for is no '
                        'longer accessible, because the parent question '
                        'has been removed'
                       )
            raise exceptions.QuestionHidden(message)
        except exceptions.AnswerHidden:
            message = _(
                        'Sorry, the comment you are looking for is no '
                        'longer accessible, because the parent answer '
                        'has been removed'
                       )
            raise exceptions.AnswerHidden(message)


    def assert_is_visible_to(self, user):
        if self.is_question():
            return self._question__assert_is_visible_to(user)
        elif self.is_answer():
            return self._answer__assert_is_visible_to(user)
        elif self.is_comment():
            return self._comment__assert_is_visible_to(user)
        raise NotImplementedError

    def get_updated_activity_data(self, created = False):
        if self.is_answer():
            #todo: simplify this to always return latest revision for the second
            #part
            if created:
                return const.TYPE_ACTIVITY_ANSWER, self
            else:
                latest_revision = self.get_latest_revision()
                return const.TYPE_ACTIVITY_UPDATE_ANSWER, latest_revision
        elif self.is_question():
            if created:
                return const.TYPE_ACTIVITY_ASK_QUESTION, self
            else:
                latest_revision = self.get_latest_revision()
                return const.TYPE_ACTIVITY_UPDATE_QUESTION, latest_revision
        elif self.is_comment():
            if self.parent.post_type == 'question':
                return const.TYPE_ACTIVITY_COMMENT_QUESTION, self
            elif self.parent.post_type == 'answer':
                return const.TYPE_ACTIVITY_COMMENT_ANSWER, self

        raise NotImplementedError

    def get_tag_names(self):
        return self.thread.get_tag_names()

    def _answer__apply_edit(self, edited_at=None, edited_by=None, text=None, comment=None, wiki=False):

        if text is None:
            text = self.get_latest_revision().text
        if edited_at is None:
            edited_at = datetime.datetime.now()
        if edited_by is None:
            raise Exception('edited_by is required')

        self.last_edited_at = edited_at
        self.last_edited_by = edited_by
        #self.html is denormalized in save()
        self.text = text
        #todo: bug wiki has no effect here

        #must add revision before saving the answer
        self.add_revision(
            author = edited_by,
            revised_at = edited_at,
            text = text,
            comment = comment
        )

        self.parse_and_save(author = edited_by)

        self.thread.set_last_activity(last_activity_at=edited_at, last_activity_by=edited_by)

    def _question__apply_edit(self, edited_at=None, edited_by=None, title=None,\
                              text=None, comment=None, tags=None, wiki=False,\
                              edit_anonymously = False, featurepic=None, is_charged=False,\
                              cost=0, subtitle=None,passcode=None,):

        latest_revision = self.get_latest_revision()
        #a hack to allow partial edits - important for SE loader
        if title is None:
            title = self.thread.title
        if text is None:
            text = latest_revision.text
        if tags is None:
            tags = latest_revision.tagnames

        if edited_by is None:
            raise Exception('parameter edited_by is required')

        if edited_at is None:
            edited_at = datetime.datetime.now()

        # Update the Question itself
        self.last_edited_at = edited_at
        self.last_edited_by = edited_by
        self.featurepic = featurepic
        self.is_charged = is_charged
        self.cost = cost
        self.text = text
        self.is_anonymous = edit_anonymously
        self.featurepic = self._check_and_reset_featurepic(featurepic)
        #wiki is an eternal trap whence there is no exit
        if self.wiki == False and wiki == True:
            self.wiki = True

        # Update the Question tag associations
        if latest_revision.tagnames != tags:
            self.thread.update_tags(tagnames = tags, user = edited_by, timestamp = edited_at)

        self.thread.title = title
        self.thread.subtitle = subtitle
        self.thread.passcode = passcode
        self.thread.tagnames = tags
        self.thread.save()

        # Create a new revision
        self.add_revision(        # has to be called AFTER updating the thread, otherwise it doesn't see new tags and the new title
            author = edited_by,
            text = text,
            revised_at = edited_at,
            is_anonymous = edit_anonymously,
            comment = comment,
            featurepic = self.featurepic,
        )

        self.parse_and_save(author = edited_by)
        # Clean the cache
        cache.cache.delete(self.thread.SUMMARY_CACHE_KEY_TPL % self.id)
        cache.cache.delete(self.thread.SUMMARY_TWMODE_CACHE_KEY_TPL % self.id)
        self.thread.set_last_activity(last_activity_at=edited_at, last_activity_by=edited_by)
    
    def increase_view_count(self, increment=1):
        owner = self.author
        owner.views=owner.views + increment
        owner.save()
        ####################################################################
        #self.update_summary_html() # regenerate question/thread summary html => seems modify to thread.update_summary_html()
        ####################################################################
        
    def increase_responses_count(self, increment=1):
        owner = self.author
        owner.responses=owner.responses + increment
        owner.save()
        ####################################################################
        #self.update_summary_html() # regenerate question/thread summary html => seems modify to thread.update_summary_html()
        ####################################################################
        
    def apply_edit(self, *kargs, **kwargs):
        if self.is_answer():
            return self._answer__apply_edit(*kargs, **kwargs)
        elif self.is_question():
            return self._question__apply_edit(*kargs, **kwargs)
        raise NotImplementedError

    def _answer__add_revision(self, author=None, revised_at=None, text=None, comment=None):
        #todo: this may be identical to Question.add_revision
        if None in (author, revised_at, text):
            raise Exception('arguments author, revised_at and text are required')
        rev_no = self.revisions.all().count() + 1
        if comment in (None, ''):
            if rev_no == 1:
                comment = const.POST_STATUS['default_version']
            else:
                comment = 'No.%s Revision' % rev_no
        from askbot.models.post import PostRevision
        return PostRevision.objects.create_answer_revision(
            post=self,
            author=author,
            revised_at=revised_at,
            text=text,
            summary=comment,
            revision=rev_no,
            featurepic = None
        )

    def _question__add_revision(
            self,
            author = None,
            is_anonymous = False,
            text = None,
            comment = None,
            revised_at = None,
            featurepic = None
    ):
        if None in (author, text, comment):
            raise Exception('author, text and comment are required arguments')
        rev_no = self.revisions.all().count() + 1
        if comment in (None, ''):
            if rev_no == 1:
                comment = const.POST_STATUS['default_version']
            else:
                comment = 'No.%s Revision' % rev_no

        from askbot.models.post import PostRevision
        return PostRevision.objects.create_question_revision(
            post = self,
            revision   = rev_no,
            title      = self.thread.title,
            author     = author,
            is_anonymous = is_anonymous,
            revised_at = revised_at,
            tagnames   = self.thread.tagnames,
            summary    = comment,
            text       = text,
            featurepic = featurepic
        )

    def add_revision(self, *kargs, **kwargs):
        if self.is_answer():
            return self._answer__add_revision(*kargs, **kwargs)
        elif self.is_question():
            return self._question__add_revision(*kargs, **kwargs)
        raise NotImplementedError

    def _answer__get_response_receivers(self, exclude_list = None):
        """get list of users interested in this response
        update based on their participation in the question
        activity

        exclude_list is required and normally should contain
        author of the updated so that he/she is not notified of
        the response
        """
        assert(exclude_list is not None)
        recipients = set()
        recipients.update(
            self.get_author_list(
                include_comments = True
            )
        )
        question = self.thread._question_post()
        recipients.update(
            question.get_author_list(
                include_comments = True
            )
        )
        for answer in question.thread.posts.get_answers().all():
            recipients.update(answer.get_author_list())

        recipients -= set(exclude_list)

        return list(recipients)

    def _question__get_response_receivers(self, exclude_list = None):
        """returns list of users who might be interested
        in the question update based on their participation
        in the question activity

        exclude_list is mandatory - it normally should have the
        author of the update so the he/she is not notified about the update
        """
        assert(exclude_list != None)
        recipients = set()
        recipients.update(
            self.get_author_list(
                include_comments = True
            )
        )
        #do not include answer commenters here
        for a in self.thread.posts.get_answers().all():
            recipients.update(a.get_author_list())

        recipients -= set(exclude_list)
        return recipients

    def _comment__get_response_receivers(self, exclude_list = None):
        """Response receivers are commenters of the
        same post and the authors of the post itself.
        """
        assert(exclude_list is not None)
        users = set()
        #get authors of parent object and all associated comments
        users.update(
            self.parent.get_author_list(
                    include_comments = True,
                )
        )
        users -= set(exclude_list)
        return list(users)


    def get_response_receivers(self, exclude_list = None):
        if self.is_answer():
            return self._answer__get_response_receivers(exclude_list)
        elif self.is_question():
            return self._question__get_response_receivers(exclude_list)
        elif self.is_comment():
            return self._comment__get_response_receivers(exclude_list)
        raise NotImplementedError

    def get_question_title(self):
        if self.is_question():
            if self.thread.closed:
                attr = const.POST_STATUS['closed']
            elif self.deleted:
                attr = const.POST_STATUS['deleted']
            else:
                attr = None
            if attr is not None:
                return u'%s %s' % (self.thread.title, attr)
            else:
                return self.thread.title
        raise NotImplementedError

    def accepted(self):
        if self.is_answer():
            return self.thread.accepted_answer_id == self.id
        raise NotImplementedError

    def get_page_number(self, answer_posts):
        """When question has many answers, answers are
        paginated. This function returns number of the page
        on which the answer will be shown, using the default
        sort order. The result may depend on the visitor."""
        if not self.is_answer() and not self.is_comment():
            raise NotImplementedError

        if self.is_comment():
            post = self.parent
        else:
            post = self

        order_number = 0
        for answer_post in answer_posts:
            if post == answer_post:
                break
            order_number += 1
        return int(order_number/const.ANSWERS_PAGE_SIZE) + 1

    def get_order_number(self):
        if not self.is_comment():
            raise NotImplementedError
        return self.parent.comments.filter(added_at__lt = self.added_at).count() + 1

    def is_upvoted_by(self, user):
        from askbot.models.meta import Vote
        return Vote.objects.filter(user=user, voted_post=self, vote=Vote.VOTE_UP).exists()

    def is_last(self):
        """True if there are no newer comments on
        the related parent object
        """
        if not self.is_comment():
            raise NotImplementedError
        return Post.objects.get_comments().filter(
            added_at__gt=self.added_at,
            parent=self.parent
        ).exists() is False

    def hack_template_marker(self, name):
        list(Post.objects.filter(text=name))


class PostRevisionManager(models.Manager):
    def create(self, *kargs, **kwargs):
        raise NotImplementedError  # Prevent accidental creation of PostRevision instance without `revision_type` set

    def create_question_revision(self, *kargs, **kwargs):
        kwargs['revision_type'] = self.model.QUESTION_REVISION
        return super(PostRevisionManager, self).create(*kargs, **kwargs)

    def create_answer_revision(self, *kargs, **kwargs):
        kwargs['revision_type'] = self.model.ANSWER_REVISION
        return super(PostRevisionManager, self).create(*kargs, **kwargs)

    def question_revisions(self):
        return self.filter(revision_type=self.model.QUESTION_REVISION)

    def answer_revisions(self):
        return self.filter(revision_type=self.model.ANSWER_REVISION)


class PostRevision(models.Model):
    QUESTION_REVISION_TEMPLATE_NO_TAGS = (
        '<h3>%(title)s</h3>\n'
        '<div class="text">%(html)s</div>\n'
    )

    QUESTION_REVISION = 1
    ANSWER_REVISION = 2
    REVISION_TYPE_CHOICES = (
        (QUESTION_REVISION, 'question'),
        (ANSWER_REVISION, 'answer'),
    )
    REVISION_TYPE_CHOICES_DICT = dict(REVISION_TYPE_CHOICES)

    post = models.ForeignKey('askbot.Post', related_name='revisions', null=True, blank=True)

    revision_type = models.SmallIntegerField(choices=REVISION_TYPE_CHOICES) # TODO: remove as we have Post now

    revision   = models.PositiveIntegerField()
    author     = models.ForeignKey('auth.User', related_name='%(class)ss')
    revised_at = models.DateTimeField()
    featurepic = models.TextField(null=True, blank=True)
    summary    = models.CharField(max_length=300, blank=True)
    text       = models.TextField(null=True)

    # Question-specific fields
    title      = models.CharField(max_length=300, blank=True, default='')
    tagnames   = models.CharField(max_length=125, blank=True, default='')
    is_anonymous = models.BooleanField(default=False)

    objects = PostRevisionManager()

    class Meta:
        # INFO: This `unique_together` constraint might be problematic for databases in which
        #       2+ NULLs cannot be stored in an UNIQUE column.
        #       As far as I know MySQL, PostgreSQL and SQLite allow that so we're on the safe side.
        unique_together = ('post', 'revision')
        ordering = ('-revision',)
        app_label = 'askbot'
        verbose_name = _('PostRevision')
        verbose_name_plural = _('PostRevision')
        
    def revision_type_str(self):
        return self.REVISION_TYPE_CHOICES_DICT[self.revision_type]

    def __unicode__(self):
        return u'%s - revision %s of %s' % (self.revision_type_str(), self.revision, self.title)

    def parent(self):
        return self.post

    def clean(self):
        "Internal cleaning method, called from self.save() by self.full_clean()"
        # TODO: Remove this when we remove `revision_type`
        if not self.post:
            raise ValidationError('Post field has to be set.')

        if (self.post.post_type == 'question' and not self.is_question_revision()) or \
           (self.post.post_type == 'answer' and not self.is_answer_revision()):
            raise ValidationError('Revision_type doesn`t match values in question/answer fields.')

    def save(self, **kwargs):
        # Determine the revision number, if not set
        if not self.revision:
            # TODO: Maybe use Max() aggregation? Or `revisions.count() + 1`
            self.revision = self.parent().revisions.values_list('revision', flat=True)[0] + 1

        # Make sure that everything is ok, in particular that `revision_type` and `revision` are set to valid values
        self.full_clean()

        super(PostRevision, self).save(**kwargs)

    def is_question_revision(self):
        return self.revision_type == self.QUESTION_REVISION

    def is_answer_revision(self):
        return self.revision_type == self.ANSWER_REVISION

    @models.permalink
    def get_absolute_url(self):
        if self.is_question_revision():
            return 'question_revisions', (self.question.id,), {}
        elif self.is_answer_revision():
            return 'answer_revisions', (), {'id':self.answer.id}

    def get_question_title(self):
        #INFO: ack-grepping shows that it's only used for Questions, so there's no code for Answers
        return self.question.thread.title

    def as_html(self, **kwargs):
        markdowner = markup.get_parser()
        sanitized_html = sanitize_html(markdowner.convert(self.text))

        if self.is_question_revision():
            return self.QUESTION_REVISION_TEMPLATE_NO_TAGS % {
                'title': self.title,
                'html': sanitized_html
            }
        elif self.is_answer_revision():
            return sanitized_html
