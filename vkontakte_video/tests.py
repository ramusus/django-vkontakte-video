# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils import timezone
import json
import mock

from vkontakte_groups.factories import GroupFactory
from vkontakte_users.factories import UserFactory, User

from factories import AlbumFactory, VideoFactory
from models import Album, Video, Comment
#from datetime import datetime
#import mock
GROUP_ID = 16297716  # https://vk.com/cocacola
ALBUM_ID = 50850761  # 9 videos
VIDEO_ID = 166742757  # 12 comments

GROUP_CRUD_ID = 59154616  # https://vk.com/club59154616 # django-vkontakte-wall crud operations
ALBUM_CRUD_ID = 55964907
VIDEO_CRUD_ID = 170947024
#USER_AUTHOR_ID = 201164356


class AlbumTest(TestCase):

    def test_fetch_group_albums(self):

        group = GroupFactory(remote_id=GROUP_ID)

        self.assertEqual(Album.objects.count(), 0)

        albums = Album.remote.fetch(group=group)

        self.assertTrue(len(albums) > 0)
        self.assertEqual(Album.objects.count(), len(albums))
        self.assertEqual(albums[0].group, group)

    def test_fetch_with_count_and_offset(self):
        # testing `count` parameter, count is the same as limit
        group = GroupFactory(remote_id=GROUP_ID)

        self.assertEqual(Album.objects.count(), 0)

        albums = Album.remote.fetch(group=group, count=5)

        self.assertEqual(len(albums), 5)
        self.assertEqual(Album.objects.count(), 5)

        # testing `offset` parameter
        albums2 = Album.remote.fetch(group=group, count=2, offset=4)

        self.assertEqual(len(albums2), 2)
        self.assertEqual(Album.objects.count(), 6)

        self.assertEqual(albums[4].remote_id, albums2[0].remote_id)

    def test_parse_album(self):

        group = GroupFactory(remote_id=GROUP_ID)

        d = {u'count': 16, u'photo_320': u'http://cs619722.vk.me/u8704019/video/l_6369beb6.jpg', u'title': u'Coca-Cola Football',
             u'photo_160': u'http://cs619722.vk.me/u8704019/video/m_ef3493e1.jpg', u'id': 54387280, u'owner_id': -16297716}

        instance = Album()
        instance.parse(d)
        instance.save()

        self.assertEqual(instance.group, group)

        self.assertEqual(instance.pk, d['id'])
        self.assertEqual(instance.title, d['title'])
        self.assertEqual(instance.videos_count, d['count'])
        self.assertEqual(instance.photo_160, d['photo_160'])


class VideoTest(TestCase):

    def test_album_fetch_videos(self):

        group = GroupFactory(remote_id=GROUP_ID)
        #album = AlbumFactory(remote_id=ALBUM_ID, group=group)

        albums = Album.remote.fetch(group=group)   # have to fetch for album.videos_count
        album = Album.objects.get(remote_id=ALBUM_ID)

        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos()  # extended=True

        self.assertTrue(len(videos) > 0)
        self.assertEqual(album.videos_count, len(videos))
        self.assertEqual(Video.objects.count(), len(videos))
        self.assertEqual(videos[0].group, group)
        self.assertEqual(videos[0].album, album)
        #self.assertTrue(videos[0].likes_count > 0)
        self.assertTrue(videos[0].comments_count > 0)

        # testing `after` parameter
        after = Video.objects.order_by('-date')[4].date

        Video.objects.all().delete()
        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos(after=after)
        self.assertEqual(len(videos), Video.objects.count())
        self.assertEqual(len(videos), 5)

        date = videos[0].date
        self.assertGreaterEqual(date, after)

        # testing `before` parameter
        before = Video.objects.order_by('-date')[2].date

        Video.objects.all().delete()
        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos(before=before, after=after)
        self.assertEqual(len(videos), Video.objects.count())
        self.assertEqual(len(videos), 3)

        date = videos[0].date
        self.assertGreaterEqual(date, after)

        date = videos.last().date
        self.assertLessEqual(date, before)

    def test_fetch_with_count_and_offset(self):
        # testing `count` parameter, count is the same as limit
        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)

        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos(count=5)

        self.assertEqual(len(videos), 5)
        self.assertEqual(Video.objects.count(), 5)

        # testing `offset` parameter
        videos2 = album.fetch_videos(count=2, offset=4)

        self.assertEqual(len(videos2), 2)
        self.assertEqual(Video.objects.count(), 6)

        self.assertEqual(videos[4].remote_id, videos2[0].remote_id)

    def test_fetch_videos_by_ids(self):
        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)

        self.assertEqual(Video.objects.count(), 0)

        videos = Video.remote.fetch(group=group, ids=[VIDEO_ID])

        self.assertEqual(len(videos), 1)
        #self.assertEqual(album.videos_count, 1)
        self.assertEqual(Video.objects.count(), 1)
        self.assertEqual(videos[0].group, group)
        self.assertEqual(videos[0].album, album)

        # fetch by album parameter
        videos = Video.remote.fetch(album=album, ids=[VIDEO_ID])
        self.assertEqual(len(videos), 1)

    def test_parse_video(self):

        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)

        response = '''{"photo_130": "http://cs313422.vk.me/u163668241/video/s_6819a7d1.jpg",
            "repeat": 0,
            "photo_320": "http://cs313422.vk.me/u163668241/video/l_4cc8a38a.jpg",
            "description": "bla bla bla",
            "title": "Эстафета Олимпийского огня «Сочи 2014». Неделя 3-я",
            "can_repost": 1, "views": 928, "album_id": 50850761, "comments": 12, "player": "http://www.youtube.com/embed/UmDAmM53bU0", "date": 1386074580, "likes": {"count": 191, "user_likes": 0}, "duration": 206, "can_comment": 1, "id": 166742757, "owner_id": -16297716}
        '''
        d = json.loads(response)

        instance = Video()
        instance.parse(d)
        instance.save()

        self.assertEqual(instance.album, album)
        self.assertEqual(instance.group, group)

        self.assertEqual(instance.remote_id, d['id'])
        self.assertEqual(instance.title, d['title'])
        self.assertEqual(instance.description, d['description'])
        self.assertEqual(instance.photo_130, d['photo_130'])
        self.assertEqual(instance.player, d['player'])
        self.assertEqual(instance.views_count, d['views'])
        self.assertEqual(instance.comments_count, d['comments'])
        self.assertEqual(instance.duration, d['duration'])

        self.assertIsNotNone(instance.date)


class CommentTest(TestCase):

    def setUp(self):
        self.objects_to_delete = []

    def tearDown(self):
        for object in self.objects_to_delete:
            object.delete(commit_remote=True)

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory.create(remote_id=i) for i in ids]]))
    def test_video_fetch_comments(self, *kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        #album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        # not factory coz we need video.comments_count later
        video = Video.remote.fetch(group=group, ids=[VIDEO_ID])[0]

        comments = video.fetch_comments(count=10, sort='desc')
        self.assertEqual(len(comments), video.comments.count())
        self.assertEqual(len(comments), 10)

        # testing `after` parameter
        after = Comment.objects.order_by('-date')[2].date

        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = video.fetch_comments(after=after, sort='desc')
        self.assertEqual(len(comments), Comment.objects.count())
        self.assertEqual(len(comments), video.comments.count())
        self.assertEqual(len(comments), 3)

        date = comments[0].date
        self.assertGreaterEqual(date, after)

        # testing `all` parameter
        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = video.fetch_comments(all=True)
        self.assertEqual(len(comments), Comment.objects.count())
        self.assertEqual(len(comments), video.comments.count())
        self.assertEqual(len(comments), video.comments_count)
        self.assertTrue(video.comments.count() > 10)

    def test_fetch_with_count_and_offset(self):
        # testing `count` parameter, count is the same as limit
        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        video = VideoFactory(remote_id=VIDEO_ID, album=album, group=group)

        self.assertEqual(Comment.objects.count(), 0)

        comments = video.fetch_comments(count=5)

        self.assertEqual(len(comments), 5)
        self.assertEqual(Comment.objects.count(), 5)

        # testing `offset` parameter
        comments2 = video.fetch_comments(count=2, offset=4)

        self.assertEqual(len(comments2), 2)
        self.assertEqual(Comment.objects.count(), 6)

        self.assertEqual(comments[4].remote_id, comments2[0].remote_id)

    #@mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory.create(remote_id=i) for i in ids]]))
    def test_video_fetch_likes(self, *kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        video = VideoFactory(remote_id=VIDEO_ID, album=album, group=group)

        self.assertEqual(video.likes_count, 0)
        users_initial = User.objects.count()

        users = video.fetch_likes(all=True)

        self.assertTrue(video.likes_count > 0)
        self.assertEqual(video.likes_count, len(users))
        self.assertEqual(video.likes_count, User.objects.count() - users_initial)
        self.assertEqual(video.likes_count, video.like_users.count())

    def test_comment_crud_methods(self):
        group = GroupFactory(remote_id=GROUP_CRUD_ID)
        album = AlbumFactory(remote_id=ALBUM_CRUD_ID, group=group)
        video = VideoFactory(remote_id=VIDEO_CRUD_ID, album=album, group=group)

        def assert_local_equal_to_remote(comment):
            comment_remote = Comment.remote.fetch_by_video(video=comment.video).get(remote_id=comment.remote_id)
            self.assertEqual(comment_remote.remote_id, comment.remote_id)
            self.assertEqual(comment_remote.text, comment.text)
            self.assertEqual(comment_remote.author, comment.author)

        Comment.remote.fetch_by_video(video=video)
        self.assertEqual(Comment.objects.count(), 0)

        # create
        comment = Comment(text='Test comment', video=video, author=group, date=timezone.now())
        comment.save(commit_remote=True)
        self.objects_to_delete += [comment]

        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.author, group)
        self.assertNotEqual(len(comment.remote_id), 0)
        assert_local_equal_to_remote(comment)

        # create by manager
        comment = Comment.objects.create(
            text='Test comment created by manager', video=video, author=group, date=timezone.now(), commit_remote=True)
        self.objects_to_delete += [comment]
        self.assertEqual(Comment.objects.count(), 2)

        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(comment.author, group)
        self.assertNotEqual(len(comment.remote_id), 0)
        assert_local_equal_to_remote(comment)

        # update
        comment.text = 'Test comment updated'
        comment.save(commit_remote=True)

        self.assertEqual(Comment.objects.count(), 2)
        assert_local_equal_to_remote(comment)

        # delete
        comment.delete(commit_remote=True)

        self.assertEqual(Comment.objects.count(), 2)
        self.assertTrue(comment.archived)
        self.assertEqual(Comment.remote.fetch_by_video(
            video=comment.video).filter(remote_id=comment.remote_id).count(), 0)

        # restore
        comment.restore(commit_remote=True)
        self.assertFalse(comment.archived)

        self.assertEqual(Comment.objects.count(), 2)
        assert_local_equal_to_remote(comment)

    def test_parse_comment(self):

        response = u'''{"date": 1387304612,
            "text": "Даёшь \\"Байкал\\"!!!!",
            "likes": {"count": 0, "can_like": 1, "user_likes": 0},
            "id": 811,
            "from_id": 27224390}
        '''

        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        video = VideoFactory(remote_id=VIDEO_ID, album=album, group=group)

        instance = Comment(video=video)
        instance.parse(json.loads(response))
        instance.save()

        self.assertEqual(instance.remote_id, '-%s_811' % GROUP_ID)  # TODO: '4_811'
        self.assertEqual(instance.video, video)
        self.assertEqual(instance.author.remote_id, 27224390)
        self.assertEqual(instance.text, u'Даёшь "Байкал"!!!!')
        self.assertIsNotNone(instance.date)


class OtherTests(TestCase):

    def test_fetch_by_user_parameter(self):
        user = UserFactory(remote_id=13312307)

        # fetch albums
        albums = Album.remote.fetch(user=user)
        self.assertGreater(len(albums), 0)
        self.assertEqual(Album.objects.count(), len(albums))
        self.assertEqual(albums[0].owner, user)

        # fetch album videos
        album = albums[0]
        videos = album.fetch_videos()
        self.assertGreater(len(videos), 0)
        self.assertEqual(Video.objects.count(), len(videos))
        self.assertEqual(videos[0].owner, user)

        # fetch user video comments
        video = videos[0]
        comments = video.fetch_comments()
        self.assertGreater(len(comments), 0)
        self.assertEqual(Comment.objects.count(), len(comments))
        self.assertEqual(comments[0].author, user)

        # fetch user video likes
        users = video.fetch_likes(all=True)
        self.assertTrue(video.likes_count > 0)
        self.assertEqual(video.likes_count, len(users))

        # fetch all user videos
        videos = Video.remote.fetch(user=user)
        self.assertGreater(len(videos), 0)
        self.assertEqual(Video.objects.count(), len(videos))
        self.assertEqual(videos[0].owner, user)

    def test_link(self):
        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        video = VideoFactory(remote_id=VIDEO_ID, album=album, group=group)

        self.assertEqual(album.link.count("-"), 1)
        self.assertEqual(video.link.count("-"), 1)

        user = UserFactory(remote_id=13312307)
        album = AlbumFactory(remote_id=55976289, owner=user)
        video = VideoFactory(remote_id=165144348, album=album, owner=user)

        self.assertEqual(album.link.count("-"), 0)
        self.assertEqual(video.link.count("-"), 0)


class OldTests():

    def test_fetch_photo_likes_parser(self):

        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        photo = PhotoFactory(remote_id=PHOTO_ID, album=album)

        self.assertEqual(photo.likes_count, 0)
        photo.fetch_likes_parser()
        self.assertTrue(photo.likes_count > 0)

    def test_fetch_photo_comments_parser(self):

        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        photo = PhotoFactory(remote_id=PHOTO_ID, album=album)

        self.assertEqual(photo.comments_count, 0)
        photo.fetch_comments_parser()
        self.assertTrue(photo.comments_count > 0)
