# -*- coding: utf-8 -*-
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
import logging
import re

from vkontakte_api.decorators import fetch_all
from vkontakte_api.mixins import CountOffsetManagerMixin, AfterBeforeManagerMixin, OwnerableModelMixin
from vkontakte_api.models import VkontakteManager, VkontakteTimelineManager, \
    VkontakteModel, VkontaktePKModel, VkontakteCRUDModel
from vkontakte_groups.models import Group
from vkontakte_comments.models import Comment

from vkontakte_users.models import User
#import signals
log = logging.getLogger('vkontakte_video')
'''
ALBUM_PRIVACY_CHOCIES = (
    (0, u'Все пользователи'),
    (1, u'Только друзья'),
    (2, u'Друзья и друзья друзей'),
    (3, u'Только я')
)
'''


class AlbumRemoteManager(CountOffsetManagerMixin):

    #timeline_force_ordering = True

    def get_timeline_date(self, instance):
        return instance.updated or instance.created or timezone.now()

    @transaction.commit_on_success
    def fetch(self, owner=None, **kwargs):
        if not owner:
            raise ValueError("You must specify owner, which albums you want to fetch")

        if owner._meta.model_name == 'user':
            kwargs['owner_id'] = owner.remote_id
        else:
            kwargs['owner_id'] = -1 * owner.remote_id

        kwargs['extended'] = 1

        return super(AlbumRemoteManager, self).fetch(**kwargs)


class VideoRemoteManager(CountOffsetManagerMixin, AfterBeforeManagerMixin):

    @transaction.commit_on_success
    def fetch(self, album=None, owner=None, ids=None, **kwargs):
        if not (album or owner):
            raise ValueError("You must specify or video album or owner, which video you want to fetch")

        if owner:
            if owner._meta.model_name == 'user':
                kwargs['owner_id'] = owner.remote_id
            else:
                kwargs['owner_id'] = -1 * owner.remote_id

        if album:
            kwargs['owner_id'] = album.remote_owner_id
            kwargs['album_id'] = album.remote_id
            #kwargs['extra_fields'] = {'album_id': album.pk}

        if ids:
            videos = []
            owner_id = kwargs['owner_id']
            for id in ids:
                vid = '%s_%s' % (owner_id, id)
                videos.append(vid)

            kwargs['videos'] = ','.join(videos)

        kwargs['extended'] = 1

        return super(VideoRemoteManager, self).fetch(**kwargs)


@python_2_unicode_compatible
class Album(OwnerableModelMixin, VkontaktePKModel):

    methods_namespace = 'video'
    #slug_prefix = 'album'

    photo_160 = models.URLField(max_length=255, default='')

    videos_count = models.PositiveIntegerField(u'Кол-во видеозаписей')

    title = models.CharField(max_length='200')

    objects = models.Manager()
    remote = AlbumRemoteManager(remote_pk=('remote_id',), version=5.27, methods={
        'get': 'getAlbums',
    })

    class Meta:
        get_latest_by = 'remote_id'
        verbose_name = u'Альбом видеозаписей Вконтакте'
        verbose_name_plural = u'Альбомы видеозаписей Вконтакте'

    def __str__(self):
        return self.title

    @property
    def link(self):
        return 'https://vk.com/videos%s?section=album_%s' % (self.remote_owner_id, self.remote_id)

    def parse(self, response):
        super(Album, self).parse(response)
        self.videos_count = response['count']

    @transaction.commit_on_success
    def fetch_videos(self, *args, **kwargs):
        return Video.remote.fetch(album=self, *args, **kwargs)


@python_2_unicode_compatible
class Video(OwnerableModelMixin, VkontaktePKModel):

    methods_namespace = 'video'

    album = models.ForeignKey(Album, null=True, related_name='videos')

    like_users = models.ManyToManyField(User, related_name='like_videos')

    title = models.CharField(max_length=255)
    description = models.TextField()

    duration = models.PositiveIntegerField(u'Продолжительность')

    likes_count = models.PositiveIntegerField(u'Лайков', default=0)
    comments_count = models.PositiveIntegerField(u'Кол-во комментариев', default=0)
    views_count = models.PositiveIntegerField(u'Кол-во просмотров', default=0)

    link = models.URLField(max_length=255)
    photo_130 = models.URLField(max_length=255)
    player = models.URLField(max_length=255)

    date = models.DateTimeField(help_text=u'Дата создания', db_index=True)

    objects = models.Manager()
    remote = VideoRemoteManager(remote_pk=('remote_id',), version=5.27, methods={
        'get': 'get',
    })

    @property
    def comments(self):
        # TODO: set this attr by related_name
        return Comment.objects.filter(object_id=self.pk,
                                      object_content_type=ContentType.objects.get_for_model(self._meta.model))

    class Meta:
        get_latest_by = 'remote_id'
        verbose_name = u'Видеозапись Вконтакте'
        verbose_name_plural = u'Видеозаписи Вконтакте'

    def __str__(self):
        return self.title

    @property
    def link(self):
        return 'https://vk.com/video%s_%s' % (self.remote_owner_id, self.remote_id)

    def parse(self, response):
        super(Video, self).parse(response)
        self.comments_count = response['comments']
        self.views_count = response['views']
        self.album_id = response.get('album_id', None)

    @transaction.commit_on_success
    def fetch_comments(self, *args, **kwargs):
        return Comment.remote.fetch_by_object(object=self, *args, **kwargs)

    #@transaction.commit_on_success
    def fetch_likes(self, *args, **kwargs):

#        kwargs['offset'] = int(kwargs.pop('offset', 0))
        kwargs['likes_type'] = 'video'
        kwargs['item_id'] = self.remote_id
        kwargs['owner_id'] = self.remote_owner_id

        log.debug('Fetching likes of %s %s of owner "%s"' % (self._meta.module_name, self.remote_id, self.owner))

        users = User.remote.fetch_instance_likes(self, *args, **kwargs)

        # update self.likes
        self.likes_count = self.like_users.count()
        self.save()

        return users
