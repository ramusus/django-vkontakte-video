# -*- coding: utf-8 -*-
from datetime import datetime
from django.test import TestCase
import json

from vkontakte_groups.factories import GroupFactory
from vkontakte_users.factories import UserFactory, User

from factories import AlbumFactory, VideoFactory
from models import VideoAlbum, Video, Comment
#import mock
GROUP_ID = 16297716  # https://vk.com/cocacola
ALBUM_ID = 50850761  # 9 videos
VIDEO_ID = 166742757  # 12 comments

GROUP_CRUD_ID = 82557438  # https://vk.com/club82557438
ALBUM_CRUD_ID = 55926063
VIDEO_CRUD_ID = 170710739
#USER_AUTHOR_ID = 201164356


class VideoAlbumTest(TestCase):

    def test_fetch_group_albums(self):

        group = GroupFactory(remote_id=GROUP_ID)

        self.assertEqual(VideoAlbum.objects.count(), 0)

        albums = VideoAlbum.remote.fetch(group=group)

        self.assertTrue(len(albums) > 0)
        self.assertEqual(VideoAlbum.objects.count(), len(albums))
        self.assertEqual(albums[0].group, group)

        '''
        # check force ordering
        self.assertListEqual(list(albums), list(Album.objects.order_by('-updated')))

        # testing `after` parameter
        after = Album.objects.order_by('-updated')[10].updated.replace(tzinfo=None)

        Album.objects.all().delete()
        self.assertEqual(Album.objects.count(), 0)

        albums = group.fetch_albums(after=after)
        self.assertEqual(len(albums), Album.objects.count())
        self.assertEqual(len(albums), 11)

        # testing `before` parameter
        before = Album.objects.order_by('-updated')[5].updated.replace(tzinfo=None)

        Album.objects.all().delete()
        self.assertEqual(Album.objects.count(), 0)

        albums = group.fetch_albums(before=before, after=after)
        self.assertEqual(len(albums), Album.objects.count())
        self.assertEqual(len(albums), 5)
        '''

    def test_parse_album(self):

        group = GroupFactory(remote_id=GROUP_ID)

        d = {u'count': 16, u'photo_320': u'http://cs619722.vk.me/u8704019/video/l_6369beb6.jpg', u'title': u'Coca-Cola Football',
             u'photo_160': u'http://cs619722.vk.me/u8704019/video/m_ef3493e1.jpg', u'id': 54387280, u'owner_id': -16297716}

        instance = VideoAlbum()
        instance.parse(d)
        instance.save()

        self.assertEqual(instance.group, group)

        self.assertEqual(instance.pk, d['id'])
        self.assertEqual(instance.title, d['title'])
        self.assertEqual(instance.videos_count, d['count'])
        self.assertEqual(instance.photo_160, d['photo_160'])


class VideoTest(TestCase):

    def setUp(self):
        self.objects_to_delete = []

    def tearDown(self):
        for object in self.objects_to_delete:
            object.delete(commit_remote=True)

    def test_album_fetch_videos(self):

        group = GroupFactory(remote_id=GROUP_ID)
        #album = AlbumFactory(remote_id=ALBUM_ID, group=group)

        albums = VideoAlbum.remote.fetch(group=group)
        album = VideoAlbum.objects.get(remote_id=ALBUM_ID)

        self.assertEqual(Video.objects.count(), 0)

        videos = album.fetch_videos()  # extended=True

        self.assertTrue(len(videos) > 0)
        self.assertEqual(album.videos_count, len(videos))
        self.assertEqual(Video.objects.count(), len(videos))
        self.assertEqual(videos[0].group, group)
        self.assertEqual(videos[0].video_album, album)
        #self.assertTrue(videos[0].likes_count > 0)
        #self.assertTrue(videos[0].comments_count > 0)

        '''
        # testing `after` parameter
        after = Photo.objects.order_by('-created')[4].created.replace(tzinfo=None)

        Photo.objects.all().delete()
        self.assertEqual(Photo.objects.count(), 0)

        photos = album.fetch_photos(after=after)
        self.assertEqual(len(photos), Photo.objects.count())
        self.assertEqual(len(photos), 5)

        # testing `before` parameter
        before = Photo.objects.order_by('-created')[2].created.replace(tzinfo=None)

        Photo.objects.all().delete()
        self.assertEqual(Photo.objects.count(), 0)

        photos = album.fetch_photos(before=before, after=after)
        self.assertEqual(len(photos), Photo.objects.count())
        self.assertEqual(len(photos), 1)
        '''

    def test_fetch_videos_by_ids(self):
        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)

        self.assertEqual(Video.objects.count(), 0)

        videos = Video.remote.fetch(group=group, ids=[VIDEO_ID])

        self.assertEqual(len(videos), 1)
        #self.assertEqual(album.videos_count, 1)
        self.assertEqual(Video.objects.count(), 1)
        self.assertEqual(videos[0].group, group)
        self.assertEqual(videos[0].video_album, album)

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

        self.assertEqual(instance.video_album, album)
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

    #@mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory.create(remote_id=i) for i in ids]]))

    def test_video_fetch_comments(self, *kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        #album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        # not factory coz we need video.comments_count later
        video = Video.remote.fetch(group=group, ids=[VIDEO_ID])[0]

        comments = video.fetch_comments(count=10, sort='desc')
        self.assertEqual(len(comments), video.comments.count())
        self.assertEqual(len(comments), 10)

        # testing `after` parameter
        after = Comment.objects.order_by('date')[0].date.replace(tzinfo=None)

        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = video.fetch_comments(after=after, sort='desc')
        self.assertEqual(len(comments), Comment.objects.count())
        self.assertEqual(len(comments), video.comments.count())
        self.assertEqual(len(comments), 11)

        # testing `all` parameter
        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = video.fetch_comments(all=True)
        self.assertEqual(len(comments), Comment.objects.count())
        self.assertEqual(len(comments), video.comments.count())
        self.assertEqual(len(comments), video.comments_count)
        self.assertTrue(video.comments.count() > 10)

    #@mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory.create(remote_id=i) for i in ids]]))

    def test_video_fetch_likes(self, *kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        video = VideoFactory(remote_id=VIDEO_ID, video_album=album, group=group)

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
        video = VideoFactory(remote_id=VIDEO_CRUD_ID, video_album=album, group=group)

        def assert_local_equal_to_remote(comment):
            comment_remote = Comment.remote.fetch_by_video(video=comment.video).get(remote_id=comment.remote_id)
            self.assertEqual(comment_remote.remote_id, comment.remote_id)
            self.assertEqual(comment_remote.text, comment.text)
            self.assertEqual(comment_remote.author, comment.author)

        Comment.remote.fetch_by_video(video=video)
        self.assertEqual(Comment.objects.count(), 0)

        # create
        comment = Comment(text='Test comment', video=video, author=group, date=datetime.now())
        comment.save(commit_remote=True)
        self.objects_to_delete += [comment]

        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.author, group)
        self.assertNotEqual(len(comment.remote_id), 0)
        assert_local_equal_to_remote(comment)

        # create by manager
        comment = Comment.objects.create(
            text='Test comment created by manager', video=video, author=group, date=datetime.now(), commit_remote=True)
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
        video = VideoFactory(remote_id=VIDEO_ID, video_album=album, group=group)

        instance = Comment(video=video)
        instance.parse(json.loads(response))
        instance.save()

        # print instance.remote_owner_id
        # print instance.text

        # self.assertEqual(instance.remote_id, '-%s_811' % GROUP_ID) # TODO: '4_811'
        self.assertEqual(instance.video, video)
        self.assertEqual(instance.author.remote_id, 27224390)
        self.assertEqual(instance.text, u'Даёшь "Байкал"!!!!')
        self.assertIsNotNone(instance.date)


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
