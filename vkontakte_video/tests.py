# -*- coding: utf-8 -*-
import json

from django.test import TestCase
from django.utils import timezone
import mock
from vkontakte_comments.models import Comment
from vkontakte_groups.factories import GroupFactory
from vkontakte_users.factories import UserFactory, User

from .factories import AlbumFactory, VideoFactory
from .models import Album, Video

GROUP_ID = 16297716  # https://vk.com/cocacola
ALBUM_ID = 50850761  # 9 videos
VIDEO_ID = 166742757  # 12 comments

GROUP_CRUD_ID = 59154616  # https://vk.com/club59154616 # django-vkontakte-wall crud operations
ALBUM_CRUD_ID = 55964907
VIDEO_CRUD_ID = 170947024
USER_ID = 201164356


class VkontakteVideosTest(TestCase):

    def test_fetch_owner_albums(self):

        owner = GroupFactory(remote_id=GROUP_ID)

        self.assertEqual(Album.objects.count(), 0)

        albums = Album.remote.fetch(owner=owner)

        self.assertGreater(albums.count(), 0)
        self.assertEqual(Album.objects.count(), albums.count())
        self.assertEqual(albums[0].owner, owner)

    def test_fetch_with_count_and_offset(self):
        # testing `count` parameter, count is the same as limit
        owner = GroupFactory(remote_id=GROUP_ID)

        self.assertEqual(Album.objects.count(), 0)

        albums = Album.remote.fetch(owner=owner, count=5)

        self.assertEqual(albums.count(), 5)
        self.assertEqual(Album.objects.count(), 5)

        # testing `offset` parameter
        albums2 = Album.remote.fetch(owner=owner, count=2, offset=4)

        self.assertEqual(len(albums2), 2)
        self.assertEqual(Album.objects.count(), 6)

        self.assertEqual(albums[4].remote_id, albums2[0].remote_id)

    def test_parse_album(self):

        owner = GroupFactory(remote_id=GROUP_ID)

        d = {u'count': 16, u'photo_320': u'http://cs619722.vk.me/u8704019/video/l_6369beb6.jpg', u'title': u'Coca-Cola Football',
             u'photo_160': u'http://cs619722.vk.me/u8704019/video/m_ef3493e1.jpg', u'id': 54387280, u'owner_id': -16297716}

        instance = Album()
        instance.parse(d)
        instance.save()

        self.assertEqual(instance.owner, owner)

        self.assertEqual(instance.pk, d['id'])
        self.assertEqual(instance.title, d['title'])
        self.assertEqual(instance.videos_count, 16)
        self.assertEqual(instance.photo_160, d['photo_160'])

    def test_album_fetch_videos(self):

        owner = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, owner=owner, videos_count=0)

        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos()  # extended=True

        self.assertGreater(videos.count(), 0)
        self.assertEqual(videos.count(), album.videos_count)
        self.assertEqual(videos.count(), Video.objects.count())
        self.assertEqual(videos[0].owner, owner)
        self.assertEqual(videos[0].album, album)
        self.assertGreater(videos[0].likes_count, 0)
        self.assertGreater(videos[0].comments_count, 0)

        # testing `after` parameter
        after = Video.objects.order_by('-date')[4].date

        Video.objects.all().delete()
        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos(after=after)
        self.assertEqual(videos.count(), Video.objects.count())
        self.assertEqual(videos.count(), 5)

        date = videos[0].date
        self.assertGreaterEqual(date, after)

        # testing `before` parameter
        before = Video.objects.order_by('-date')[2].date

        Video.objects.all().delete()
        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos(before=before, after=after)
        self.assertEqual(videos.count(), Video.objects.count())
        self.assertEqual(videos.count(), 3)

        self.assertGreaterEqual(videos[0].date, after)

        self.assertLessEqual(videos.order_by('-date')[0].date, before)

    def test_fetch_with_count_and_offset(self):
        # testing `count` parameter, count is the same as limit
        owner = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, owner=owner)

        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos(count=5)

        self.assertEqual(videos.count(), 5)
        self.assertEqual(Video.objects.count(), 5)

        # testing `offset` parameter
        videos2 = album.fetch_videos(count=2, offset=4)

        self.assertEqual(len(videos2), 2)
        self.assertEqual(Video.objects.count(), 6)

        # print videos[4].remote_id
        # print videos2[0].remote_id
        # print videos2[1].remote_id

        self.assertEqual(videos[4].remote_id, videos2[0].remote_id)

    def test_fetch_videos_by_ids(self):
        owner = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, owner=owner, videos_count=0)

        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos(ids=[VIDEO_ID])

        self.assertEqual(videos.count(), 1)
        self.assertEqual(album.videos_count, 1)
        self.assertEqual(Video.objects.count(), 1)
        self.assertEqual(videos[0].owner, owner)
        self.assertEqual(videos[0].album, album)

        # fetch by album parameter
        videos = Video.remote.fetch(album=album, ids=[VIDEO_ID])
        self.assertEqual(videos.count(), 1)

    def test_parse_video(self):

        owner = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, owner=owner)

        response = '''{"photo_130": "http://cs313422.vk.me/u163668241/video/s_6819a7d1.jpg",
            "repeat": 0,
            "photo_320": "http://cs313422.vk.me/u163668241/video/l_4cc8a38a.jpg",
            "description": "bla bla bla",
            "title": "Эстафета Олимпийского огня «Сочи 2014». Неделя 3-я",
            "can_repost": 1, "views": 928, "album_id": 50850761, "comments": 12, "player": "http://www.youtube.com/embed/UmDAmM53bU0", "date": 1386074580, "likes": {"count": 191, "user_likes": 0}, "duration": 206, "can_comment": 1, "id": 166742757, "owner_id": -16297716}
        '''
        d = json.loads(response)

        instance = Video(album=album)
        instance.parse(dict(d))
        instance.save()

#        self.assertEqual(instance.album, album)
        self.assertEqual(instance.owner, owner)

        self.assertEqual(instance.remote_id, d['id'])
        self.assertEqual(instance.title, d['title'])
        self.assertEqual(instance.description, d['description'])
        self.assertEqual(instance.photo_130, d['photo_130'])
        self.assertEqual(instance.player, d['player'])
        self.assertEqual(instance.views_count, d['views'])
        self.assertEqual(instance.comments_count, d['comments'])
        self.assertEqual(instance.duration, d['duration'])

        self.assertIsNotNone(instance.date)

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory.create(remote_id=i) for i in ids]]))
    def test_video_fetch_comments(self, *kwargs):

        owner = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, owner=owner)
        video = VideoFactory(remote_id=VIDEO_ID, owner=owner, album=album, comments_count=0)

        comments = video.fetch_comments(count=10, sort='desc')
        self.assertEqual(comments.count(), video.comments.count())
        self.assertEqual(comments.count(), 10)

        # testing `after` parameter
        after = Comment.objects.order_by('-date')[2].date

        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = video.fetch_comments(after=after, sort='desc')
        self.assertEqual(comments.count(), Comment.objects.count())
        self.assertEqual(comments.count(), video.comments.count())
        self.assertEqual(comments.count(), 3)

        date = comments[0].date
        self.assertGreaterEqual(date, after)

        # testing `all` parameter
        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = video.fetch_comments(all=True)
        self.assertEqual(comments.count(), Comment.objects.count())
        self.assertEqual(comments.count(), video.comments.count())
        self.assertEqual(comments.count(), video.comments_count)
        self.assertGreater(video.comments.count(), 10)

    def test_fetch_with_count_and_offset(self):
        # testing `count` parameter, count is the same as limit
        owner = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, owner=owner)
        video = VideoFactory(remote_id=VIDEO_ID, album=album, owner=owner)

        self.assertEqual(Comment.objects.count(), 0)

        comments = video.fetch_comments(count=5)

        self.assertEqual(comments.count(), 5)
        self.assertEqual(Comment.objects.count(), 5)

        # testing `offset` parameter
        comments2 = video.fetch_comments(count=2, offset=4)

        self.assertEqual(len(comments2), 2)
        self.assertEqual(Comment.objects.count(), 6)

        self.assertEqual(comments[4].remote_id, comments2[0].remote_id)

    #@mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory.create(remote_id=i) for i in ids]]))
    def test_video_fetch_likes(self, *kwargs):

        owner = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, owner=owner)
        video = VideoFactory(remote_id=VIDEO_ID, album=album, owner=owner, likes_count=0)

        self.assertEqual(video.likes_count, 0)
        users_initial = User.objects.count()

        users = video.fetch_likes(all=True)

        self.assertGreater(video.likes_count, 0)
        self.assertEqual(video.likes_count, len(users))
        self.assertEqual(video.likes_count, User.objects.count() - users_initial)
        self.assertEqual(video.likes_count, video.likes_users.count())

    def test_fetch_user_videos(self):
        user = UserFactory(remote_id=USER_ID)

        # fetch albums
        albums = Album.remote.fetch(owner=user)
        self.assertGreater(albums.count(), 0)
        self.assertEqual(albums.count(), Album.objects.count())
        self.assertEqual(albums[0].owner, user)

        # fetch album videos
        album = albums[0]
        videos = album.fetch_videos()
        self.assertGreater(videos.count(), 0)
        self.assertEqual(videos.count(), Video.objects.count())
        self.assertEqual(videos.count(), album.videos_count)
        self.assertEqual(videos[0].owner, user)

        # fetch user video comments
        video = videos[0]
        comments = video.fetch_comments()
        self.assertGreater(comments.count(), 0)
        self.assertEqual(comments.count(), Comment.objects.count())
        self.assertEqual(comments[0].author, user)

        # fetch user video likes
        users = video.fetch_likes(all=True)
        self.assertGreater(video.likes_count, 0)
        self.assertEqual(video.likes_count, len(users))

        # fetch all user videos
        videos = Video.remote.fetch(owner=user)
        self.assertGreater(videos.count(), 0)
        self.assertGreater(videos.count(), album.videos_count)
        self.assertEqual(videos.filter(album=album).count(), album.videos_count)
        self.assertEqual(videos.count(), Video.objects.count())
        self.assertEqual(videos[0].owner, user)

    def test_get_url(self):
        owner = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, owner=owner)
        video = VideoFactory(remote_id=VIDEO_ID, album=album, owner=owner)

        self.assertEqual(album.get_url().count("-"), 1)
        self.assertEqual(video.get_url().count("-"), 1)

        user = UserFactory(remote_id=13312307)
        album = AlbumFactory(remote_id=55976289, owner=user)
        video = VideoFactory(remote_id=165144348, album=album, owner=user)

        self.assertEqual(album.get_url().count("-"), 0)
        self.assertEqual(video.get_url().count("-"), 0)
