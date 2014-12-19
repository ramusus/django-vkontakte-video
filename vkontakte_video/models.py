# -*- coding: utf-8 -*-
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
import logging
import re

from vkontakte_api.decorators import fetch_all
from vkontakte_api.models import VkontakteManager, VkontakteTimelineManager, VkontakteModel, VkontakteCRUDModel
from vkontakte_groups.models import Group
from vkontakte_users.models import User
#import signals
log = logging.getLogger('vkontakte_video')

ALBUM_PRIVACY_CHOCIES = (
    (0, u'Все пользователи'),
    (1, u'Только друзья'),
    (2, u'Друзья и друзья друзей'),
    (3, u'Только я')
)


class CountOffsetManagerMixin(VkontakteManager):

    def fetch(self, count=100, offset=0, **kwargs):
        count = int(count)
        if count > 100:
            raise ValueError("Attribute 'count' can not be more than 100")

        # count количество элементов, которое необходимо получить.
        if count:
            kwargs['count'] = count

        # offset смещение, необходимое для выборки определенного подмножества. По умолчанию — 0.
        # положительное число
        offset = int(offset)
        if offset:
            kwargs['offset'] = offset

        return super(CountOffsetManagerMixin, self).fetch(**kwargs)


class AfterBeforeManagerMixin(VkontakteTimelineManager):

    def fetch(self, before=None, after=None, **kwargs):
        if before and not after:
            raise ValueError("Attribute `before` should be specified with attribute `after`")
        if before and before < after:
            raise ValueError("Attribute `before` should be later, than attribute `after`")

        # special parameters
        if after:
            kwargs['after'] = after
        if before:
            kwargs['before'] = before

        return super(AfterBeforeManagerMixin, self).fetch(**kwargs)


class VideoAlbumRemoteManager(CountOffsetManagerMixin):

    #timeline_force_ordering = True

    def get_timeline_date(self, instance):
        return instance.updated or instance.created or timezone.now()

    @transaction.commit_on_success
    def fetch(self, user=None, group=None, **kwargs):
        if not (user or group):
            raise ValueError("You must specify user of group, which albums you want to fetch")

        if user:
            kwargs['owner_id'] = user.remote_id
        elif group:
            kwargs['owner_id'] = -1 * group.remote_id

        kwargs['extended'] = 1

        return super(VideoAlbumRemoteManager, self).fetch(**kwargs)


class VideoRemoteManager(CountOffsetManagerMixin, AfterBeforeManagerMixin):

    @transaction.commit_on_success
    def fetch(self, video_album=None, user=None, group=None, ids=None, **kwargs):
        if not (video_album or user or group):
            raise ValueError("You must specify  or video album or user or group, which video you want to fetch")

        if user:
            kwargs['owner_id'] = user.remote_id
        elif group:
            kwargs['owner_id'] = -1 * group.remote_id

        if video_album:
            kwargs['owner_id'] = video_album.remote_owner_id
            kwargs['album_id'] = video_album.remote_id
            #kwargs['extra_fields'] = {'video_album_id': video_album.pk}

        if ids:
            videos = []
            owner_id = kwargs['owner_id']
            for id in ids:
                vid = '%s_%s' % (owner_id, id)
                videos.append(vid)

            kwargs['videos'] = ','.join(videos)

        kwargs['extended'] = 1

        return super(VideoRemoteManager, self).fetch(**kwargs)


'''
class PhotoRemoteManager(VkontakteTimelineManager):

    timeline_cut_fieldname = 'created'
    timeline_force_ordering = True

    @transaction.commit_on_success
    def fetch(self, album, ids=None, limit=None, extended=False, offset=0, photo_sizes=False, before=None, rev=0, after=None, **kwargs):
        if ids and not isinstance(ids, (tuple, list)):
            raise ValueError("Attribute 'ids' should be tuple or list")
        if before and not after:
            raise ValueError("Attribute `before` should be specified with attribute `after`")
        if before and before < after:
            raise ValueError("Attribute `before` should be later, than attribute `after`")
        # TODO: it seems rev attribute make no sence for order of response
        if rev == 1 and (after or before):
            raise ValueError("Attribute `rev` should be equal to 0 with defined `after` attribute")

        kwargs = {
            'album_id': album.remote_id.split('_')[1],
            'extended': int(extended),
            'offset': int(offset),
            # photo_sizes
            # 1 - позволяет получать все размеры фотографий.
            'photo_sizes': int(photo_sizes),
        }
        if album.owner:
            kwargs.update({'uid': album.owner.remote_id})
        elif album.group:
            kwargs.update({'gid': album.group.remote_id})
        if ids:
            kwargs.update({'photo_ids': ','.join(map(str, ids))})
        if limit:
            kwargs.update({'limit': limit})

        kwargs['rev'] = int(rev)

        # special parameters
        kwargs['after'] = after
        kwargs['before'] = before

        # TODO: добавить поля
        # feed
        # Unixtime, который может быть получен методом newsfeed.get в поле date, для получения всех фотографий загруженных пользователем в определённый день либо на которых пользователь был отмечен. Также нужно указать параметр uid пользователя, с которым произошло событие.
        # feed_type
        # Тип новости получаемый в поле type метода newsfeed.get, для получения только загруженных пользователем фотографий, либо только фотографий, на которых он был отмечен. Может принимать значения photo, photo_tag.

        return super(PhotoRemoteManager, self).fetch(**kwargs)
'''


class CommentRemoteManager(CountOffsetManagerMixin, AfterBeforeManagerMixin):

    @transaction.commit_on_success
    @fetch_all(default_count=100)
    def fetch_album(self, album, sort='asc', need_likes=True, **kwargs):
        raise NotImplementedError

    @transaction.commit_on_success
    @fetch_all(default_count=100)
    def fetch_by_video(self, video, sort='asc', need_likes=True, **kwargs):
        if sort not in ['asc', 'desc']:
            raise ValueError("Attribute 'sort' should be equal to 'asc' or 'desc'")

        if 'after' in kwargs:
            if kwargs['after'] and sort == 'asc':
                raise ValueError("Attribute `sort` should be equal to 'desc' with defined `after` attribute")

        # owner_id идентификатор пользователя или сообщества, которому принадлежит фотография.
        # Обратите внимание, идентификатор сообщества в параметре owner_id необходимо указывать со знаком "-" — например, owner_id=-1 соответствует идентификатору сообщества ВКонтакте API (club1)
        # int (числовое значение), по умолчанию идентификатор текущего пользователя

        kwargs['owner_id'] = video.remote_owner_id

        # video_id идентификатор видеозаписи.
        # int (числовое значение), обязательный параметр
        kwargs['video_id'] = video.remote_id

        # need_likes 1 — будет возвращено дополнительное поле likes. По умолчанию поле likes не возвращается.
        # флаг, может принимать значения 1 или 0
        kwargs['need_likes'] = int(need_likes)

        # sort порядок сортировки комментариев (asc — от старых к новым, desc - от новых к старым)
        # строка
        kwargs['sort'] = sort

        kwargs['extra_fields'] = {'video_id': video.pk}

#        try:
        return super(CommentRemoteManager, self).fetch(**kwargs)
#         except VkontakteError, e:
#             if e.code == 100 and 'invalid tid' in e.description:
#                 log.error("Impossible to fetch comments for unexisted topic ID=%s" % topic.remote_id)
#                 return self.model.objects.none()
#             else:
#                 raise e


class VideoAbstractModel(VkontakteModel):

    methods_namespace = 'video'

    remote_id = models.BigIntegerField(u'ID', primary_key=True, help_text=u'Уникальный идентификатор', unique=True)

    class Meta:
        abstract = True

    """
    @property
    def slug(self):
        return self.slug_prefix + str(self.remote_id)

    @property
    def remote_id_short(self):
        return self.remote_id.split('_')[1]

    def get_remote_id(self, id):
        '''
        Returns unique remote_id, contains from 2 parts: remote_id of owner or group and remote_id of photo object
        TODO: перейти на ContentType и избавиться от метода
        '''
        if self.owner:
            remote_id = self.owner.remote_id
        elif self.group:
            remote_id = -1 * self.group.remote_id

        return '%s_%s' % (remote_id, id)
    """

    @property
    def remote_owner_id(self):
        if self.owner:
            return self.owner.remote_id
        else:
            return -1 * self.group.remote_id

    def parse(self, response):
        # TODO: перейти на ContentType и избавиться от метода
        owner_id = int(response.pop('owner_id'))
        if owner_id > 0:
            self.owner = User.objects.get_or_create(remote_id=owner_id)[0]
        else:
            self.group = Group.objects.get_or_create(remote_id=abs(owner_id))[0]

        super(VideoAbstractModel, self).parse(response)

        #self.remote_id = self.get_remote_id(self.remote_id)


@python_2_unicode_compatible
class VideoAlbum(VideoAbstractModel):

    #remote_pk_field = 'album_id'
    #slug_prefix = 'album'

    # TODO: migrate to ContentType framework, remove vkontakte_users and vkontakte_groups dependencies
    owner = models.ForeignKey(User, verbose_name=u'Владелец альбома', null=True, related_name='video_albums')
    group = models.ForeignKey(Group, verbose_name=u'Группа альбома', null=True, related_name='video_albums')

    photo_160 = models.URLField(max_length=255, default='')

    videos_count = models.PositiveIntegerField(u'Кол-во видеозаписей')

    title = models.CharField(max_length='200')

    objects = models.Manager()
    remote = VideoAlbumRemoteManager(remote_pk=('remote_id',), version=5.27, methods={
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
        super(VideoAlbum, self).parse(response)
        self.videos_count = response['count']

    @transaction.commit_on_success
    def fetch_videos(self, *args, **kwargs):
        return Video.remote.fetch(video_album=self, *args, **kwargs)


@python_2_unicode_compatible
class Video(VideoAbstractModel):
    #methods_namespace = 'video'
    #remote_pk_field = 'vid'

    video_album = models.ForeignKey(VideoAlbum, null=True, related_name='videos')

    # TODO: migrate to ContentType framework, remove vkontakte_users and vkontakte_groups dependencies
    owner = models.ForeignKey(User, verbose_name=u'Владелец альбома', null=True)  # , related_name='videos'
    group = models.ForeignKey(Group, verbose_name=u'Группа альбома', null=True, related_name='videos')

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
        self.video_album_id = response.get('album_id', None)

    @transaction.commit_on_success
    def fetch_comments(self, *args, **kwargs):
        return Comment.remote.fetch_by_video(video=self, *args, **kwargs)

    #@transaction.commit_on_success
    def fetch_likes(self, *args, **kwargs):

#        kwargs['offset'] = int(kwargs.pop('offset', 0))
        kwargs['likes_type'] = 'video'
        kwargs['item_id'] = self.remote_id
        kwargs['owner_id'] = self.remote_owner_id

        log.debug('Fetching likes of %s %s of owner "%s"' % (self._meta.module_name, self.remote_id, self.group))

        users = User.remote.fetch_instance_likes(self, *args, **kwargs)

        # update self.likes
        self.likes_count = self.like_users.count()
        self.save()

        return users


"""
class Photo(PhotosAbstractModel):

    remote_pk_field = 'pid'
    slug_prefix = 'photo'

    album = models.ForeignKey(Album, verbose_name=u'Альбом', related_name='photos')

    # TODO: switch to ContentType, remove owner and group foreignkeys
    owner = models.ForeignKey(User, verbose_name=u'Владелец фотографии', null=True, related_name='photos')
    group = models.ForeignKey(Group, verbose_name=u'Группа фотографии', null=True, related_name='photos')

    user = models.ForeignKey(User, verbose_name=u'Автор фотографии', null=True, related_name='photos_author')

    src = models.CharField(u'Иконка', max_length='200')
    src_big = models.CharField(u'Большая', max_length='200')
    src_small = models.CharField(u'Маленькая', max_length='200')
    src_xbig = models.CharField(u'Большая X', max_length='200')
    src_xxbig = models.CharField(u'Большая XX', max_length='200')

    width = models.PositiveIntegerField(null=True)
    height = models.PositiveIntegerField(null=True)

    likes_count = models.PositiveIntegerField(u'Лайков', default=0)
    comments_count = models.PositiveIntegerField(u'Комментариев', default=0)
    actions_count = models.PositiveIntegerField(u'Комментариев', default=0)
    tags_count = models.PositiveIntegerField(u'Тегов', default=0)

    like_users = models.ManyToManyField(User, related_name='like_photos')

    text = models.TextField()

    created = models.DateTimeField(db_index=True)

    objects = models.Manager()
    remote = PhotoRemoteManager(remote_pk=('remote_id',), methods={
        'get': 'get',
    })

    class Meta:
        verbose_name = u'Фотография Вконтакте'
        verbose_name_plural = u'Фотографии Вконтакте'

    def parse(self, response):
        super(Photo, self).parse(response)

        # counters
        for field_name in ['likes', 'comments', 'tags']:
            if field_name in response and 'count' in response[field_name]:
                setattr(self, '%s_count' % field_name, response[field_name]['count'])

        self.actions_count = self.likes_count + self.comments_count

        if 'user_id' in response:
            self.user = User.objects.get_or_create(remote_id=response['user_id'])[0]

        try:
            self.album = Album.objects.get(remote_id=self.get_remote_id(response['aid']))
        except Album.DoesNotExist:
            raise Exception('Impossible to save photo for unexisted album %s' % (self.get_remote_id(response['aid']),))

    def fetch_comments_parser(self):
        '''
        Fetch total ammount of comments
        TODO: implement fetching comments
        '''
        post_data = {
            'act': 'photo_comments',
            'al': 1,
            'offset': 0,
            'photo': self.remote_id,
        }
        parser = VkontaktePhotosParser().request('/al_photos.php', data=post_data)

        self.comments_count = len(parser.content_bs.findAll('div', {'class': 'clear_fix pv_comment '}))
        self.save()

    def fetch_likes_parser(self):
        '''
        Fetch total ammount of likes
        TODO: implement fetching users who likes
        '''
        post_data = {
            'act': 'a_get_stats',
            'al': 1,
            'list': 'album%s' % self.album.remote_id,
            'object': 'photo%s' % self.remote_id,
        }
        parser = VkontaktePhotosParser().request('/like.php', data=post_data)

        values = re.findall(r'value="(\d+)"', parser.html)
        if len(values):
            self.likes_count = int(values[0])
            self.save()

    @transaction.commit_on_success
    def fetch_likes(self, *args, **kwargs):

#        kwargs['offset'] = int(kwargs.pop('offset', 0))
        kwargs['likes_type'] = 'photo'
        kwargs['item_id'] = self.remote_id.split('_')[1]
        kwargs['owner_id'] = self.group.remote_id
        if isinstance(self.group, Group):
            kwargs['owner_id'] *= -1

        log.debug('Fetching likes of %s %s of owner "%s"' % (self._meta.module_name, self.remote_id, self.group))

        users = User.remote.fetch_instance_likes(self, *args, **kwargs)

        # update self.likes
        self.likes_count = self.like_users.count()
        self.save()

        return users

    @transaction.commit_on_success
    def fetch_comments(self, *args, **kwargs):
        return Comment.remote.fetch_photo(photo=self, *args, **kwargs)
"""


class Comment(VkontakteModel, VkontakteCRUDModel):

    methods_namespace = 'video'
    #remote_pk_field = 'cid'
    fields_required_for_update = ['comment_id', 'owner_id']
    _commit_remote = False

    remote_id = models.CharField(
        u'ID', primary_key=True, max_length=20, help_text=u'Уникальный идентификатор', unique=True)

    video = models.ForeignKey(Video, verbose_name=u'Видеозапись', related_name='comments')

    author_content_type = models.ForeignKey(ContentType, related_name='video_comments')
    author_id = models.PositiveIntegerField(db_index=True)
    author = generic.GenericForeignKey('author_content_type', 'author_id')

    date = models.DateTimeField(help_text=u'Дата создания', db_index=True)
    text = models.TextField(u'Текст сообщения')
    # attachments - присутствует только если у сообщения есть прикрепления,
    # содержит массив объектов (фотографии, ссылки и т.п.). Более подробная
    # информация представлена на странице Описание поля attachments

    # TODO: implement with tests
#    likes = models.PositiveIntegerField(u'Кол-во лайков', default=0)

    objects = models.Manager()
    remote = CommentRemoteManager(remote_pk=('remote_id',), version=5.27, methods={
        'get': 'getComments',
        'create': 'createComment',
        'update': 'editComment',
        'delete': 'deleteComment',
        'restore': 'restoreComment',
    })

    class Meta:
        verbose_name = u'Комментарий видеозаписи Вконтакте'
        verbose_name_plural = u'Комментарии видеозаписей Вконтакте'

    @property
    def remote_owner_id(self):
        # return self.photo.remote_id.split('_')[0]
        if self.video.owner:
            return self.video.owner.remote_id
        else:
            return -1 * self.video.group.remote_id

    @property
    def remote_id_short(self):
        return self.remote_id.split('_')[1]

    def prepare_create_params(self, from_group=False, **kwargs):
        if self.author == self.video.group:
            from_group = True
        kwargs.update({
            'owner_id': self.remote_owner_id,
            'video_id': self.video.remote_id,  # remote_id_short,
            'message': self.text,
#            'reply_to_comment': self.reply_for.id if self.reply_for else '',
            'from_group': int(from_group),
            'attachments': kwargs.get('attachments', ''),
        })
        return kwargs

    def prepare_update_params(self, **kwargs):
        kwargs.update({
            'owner_id': self.remote_owner_id,
            'comment_id': self.remote_id_short,
            'message': self.text,
            'attachments': kwargs.get('attachments', ''),
        })
        return kwargs

    def prepare_delete_params(self):
        return {
            'owner_id': self.remote_owner_id,
            'comment_id': self.remote_id_short
        }

    def parse_remote_id_from_response(self, response):
        if response:
            return '%s_%s' % (self.remote_owner_id, response)
        return None

    def get_or_create_group_or_user(self, remote_id):
        if remote_id > 0:
            Model = User
        elif remote_id < 0:
            Model = Group
        else:
            raise ValueError("remote_id shouldn't be equal to 0")

        return Model.objects.get_or_create(remote_id=abs(remote_id))

    def parse(self, response):
        # undocummented feature of API. if from_id == 101 -> comment by group
        if response['from_id'] == 101:
            self.author = self.video.group
        else:
            self.author = self.get_or_create_group_or_user(response.pop('from_id'))[0]

        # TODO: add parsing attachments and polls
        if 'attachments' in response:
            response.pop('attachments')
        if 'poll' in response:
            response.pop('poll')

        if 'message' in response:
            response['text'] = response.pop('message')

        super(Comment, self).parse(response)

        if '_' not in str(self.remote_id):
            self.remote_id = '%s_%s' % (self.remote_owner_id, self.remote_id)
