# -*- coding: utf-8 -*-
from django.test import TestCase
from models import Album, Photo, Comment
from factories import AlbumFactory, PhotoFactory
from vkontakte_users.factories import UserFactory, User
from vkontakte_groups.factories import GroupFactory
from datetime import datetime
import simplejson as json
import mock

GROUP_ID = 16297716
ALBUM_ID = '-16297716_154228728'
PHOTO_ID = '-16297716_280118215'

GROUP_CRUD_ID = 59154616
PHOTO_CRUD_ID = '-59154616_321155660'
ALBUM_CRUD_ID = '-59154616_180124643'
USER_AUTHOR_ID = 201164356


class VkontaktePhotosTest(TestCase):

    def setUp(self):
        self.objects_to_delete = []

    def tearDown(self):
        for object in self.objects_to_delete:
            object.delete(commit_remote=True)

    def test_fetch_group_albums(self):

        group = GroupFactory(remote_id=GROUP_ID)

        self.assertEqual(Album.objects.count(), 0)

        albums = group.fetch_albums()

        self.assertTrue(len(albums) > 0)
        self.assertEqual(Album.objects.count(), len(albums))
        self.assertEqual(albums[0].group, group)

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

    def test_fetch_group_photos(self):

        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)

        self.assertEqual(Photo.objects.count(), 0)

        photos = album.fetch_photos(extended=True)

        self.assertTrue(len(photos) > 0)
        self.assertEqual(Photo.objects.count(), len(photos))
        self.assertEqual(photos[0].group, group)
        self.assertEqual(photos[0].album, album)
        self.assertTrue(photos[0].likes_count > 0)
        self.assertTrue(photos[0].comments_count > 0)

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

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory.create(remote_id=i) for i in ids]]))
    def test_fetch_photo_comments(self, *kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        photo = PhotoFactory(remote_id=PHOTO_ID, album=album, group=group)

        comments = photo.fetch_comments(count=20, sort='desc')
        self.assertEqual(len(comments), photo.comments.count())
        self.assertEqual(len(comments), 20)

        # testing `after` parameter
        after = Comment.objects.order_by('date')[0].date.replace(tzinfo=None)

        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = photo.fetch_comments(after=after, sort='desc')
        self.assertEqual(len(comments), Comment.objects.count())
        self.assertEqual(len(comments), photo.comments.count())
        self.assertEqual(len(comments), 21)

        # testing `all` parameter
        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = photo.fetch_comments(all=True)
        self.assertEqual(len(comments), Comment.objects.count())
        self.assertEqual(len(comments), photo.comments.count())
        self.assertTrue(photo.comments.count() > 20)

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory.create(remote_id=i) for i in ids]]))
    def test_fetch_photo_likes(self, *kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        photo = PhotoFactory(remote_id=PHOTO_ID, album=album, group=group)

        self.assertEqual(photo.likes_count, 0)
        users_initial = User.objects.count()

        users = photo.fetch_likes(all=True)

        self.assertTrue(photo.likes_count > 0)
        self.assertEqual(photo.likes_count, len(users))
        self.assertEqual(photo.likes_count, User.objects.count() - users_initial)
        self.assertEqual(photo.likes_count, photo.like_users.count())

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

    def test_parse_album(self):

        response = '''{"response":[{"aid":"16178407","thumb_id":"96509883","owner_id":"6492","title":"qwerty",
            "description":"desc","created":"1298365200","updated":"1298365201","size":"3",
            "privacy":"3"},{"aid":"17071606","thumb_id":"98054577","owner_id":"-6492",
            "title":"","description":"","created":"1204576880","updated":"1229532461",
            "size":"3","privacy":"0"}]}
            '''
        instance = Album()
        owner = UserFactory(remote_id=6492)
        instance.parse(json.loads(response)['response'][0])
        instance.save()

        self.assertEqual(instance.remote_id, '6492_16178407')
        self.assertEqual(instance.thumb_id, 96509883)
        self.assertEqual(instance.owner, owner)
        self.assertEqual(instance.title, 'qwerty')
        self.assertEqual(instance.description, 'desc')
        self.assertEqual(instance.size, 3)
        self.assertEqual(instance.privacy, 3)
        self.assertIsNotNone(instance.created)
        self.assertIsNotNone(instance.updated)

        instance = Album()
        group = GroupFactory(remote_id=6492)
        instance.parse(json.loads(response)['response'][1])
        instance.save()

        self.assertEqual(instance.remote_id, '-6492_17071606')
        self.assertEqual(instance.group, group)

    def test_parse_photo(self):

        response = '''{"response":[{"pid":"146771291","aid":"100001227","owner_id":"6492",
            "src":"http://cs9231.vkontakte.ru/u06492/100001227/m_7875d2fb.jpg",
            "src_big":"http://cs9231.vkontakte.ru/u06492/100001227/x_cd563004.jpg",
            "src_small":"http://cs9231.vkontakte.ru/u06492/100001227/s_c3bba2a8.jpg",
            "src_xbig":"http://cs9231.vkontakte.ru/u06492/100001227/y_62a74569.jpg",
            "src_xxbig":"http://cs9231.vkontakte.ru/u06492/100001227/z_793e9682.jpg",
            "text":"test","user_id":6492,"width":10,"height":10,
            "created":"1298365200"},{"pid":"146772677","aid":"100001227","owner_id":-6492,
            "src":"http://cs9231.vkontakte.ru/u06492/100001227/m_fd092958.jpg",
            "src_big":"http://cs9231.vkontakte.ru/u06492/100001227/x_1f8ec9b8.jpg",
            "src_small":"http://cs9231.vkontakte.ru/u06492/100001227/s_603d27ab.jpg",
            "src_xbig":"http://cs9231.vkontakte.ru/u06492/100001227/y_6938f576.jpg",
            "src_xxbig":"http://cs9231.vkontakte.ru/u06492/100001227/z_6a27e9fd.jpg",
            "text":"test","user_id":6492,"width":10,"height":10,
            "created":"1260887080"}]}
            '''
        instance = Photo()
        owner = UserFactory(remote_id=6492)
        album = AlbumFactory(remote_id='6492_100001227')
        instance.parse(json.loads(response)['response'][0])
        instance.save()

        self.assertEqual(instance.remote_id, '6492_146771291')
        self.assertEqual(instance.album, album)
        self.assertEqual(instance.owner, owner)
        self.assertEqual(instance.src, 'http://cs9231.vkontakte.ru/u06492/100001227/m_7875d2fb.jpg')
        self.assertEqual(instance.text, 'test')
        self.assertEqual(instance.width, 10)
        self.assertEqual(instance.height, 10)
        self.assertIsNotNone(instance.created)

        instance = Photo()
        group = GroupFactory(remote_id=6492)
        album = AlbumFactory(remote_id='-6492_100001227')
        instance.parse(json.loads(response)['response'][1])
        instance.save()

        self.assertEqual(instance.remote_id, '-6492_146772677')
        self.assertEqual(instance.album, album)
        self.assertEqual(instance.group, group)

    def test_parse_comment(self):

        response = '''{"response":[21, {"date": 1387173931, "message": "[id94721323|\u0410\u043b\u0435\u043d\u0447\u0438\u043a], \u043d\u0435 1 \u0430 3 \u0431\u0430\u043d\u043a\u0430 5 \u043b\u0438\u0442\u0440\u043e\u0432 =20 \u0431\u0430\u043b\u043b\u043e\u0432", "from_id": 232760293, "likes": {"count": 1, "can_like": 1, "user_likes": 0}, "cid": 91121},
            {"date": 1386245221, "message": "\u0410 1\u043b. \u0432 \u043f\u043e\u0434\u0430\u0440\u043e\u043a,\u0431\u043e\u043d\u0443\u0441 +))))", "from_id": 94721323, "likes": {"count": 0, "can_like": 1, "user_likes": 0}, "cid": 88976},
            {"date": 1354592120, "message": "\u0445\u0430\u0445<br>", "from_id": 138571769, "likes": {"count": 0, "can_like": 1, "user_likes": 0}, "cid": 50392}]}
        '''
        group = GroupFactory(remote_id=GROUP_ID)
        album = AlbumFactory(remote_id=ALBUM_ID, group=group)
        photo = PhotoFactory(remote_id=PHOTO_ID, album=album)
        instance = Comment(photo=photo)
        instance.parse(json.loads(response)['response'][1])
        instance.save()

        self.assertEqual(instance.remote_id, '-%s_91121' % GROUP_ID)
        self.assertEqual(instance.photo, photo)
        self.assertEqual(instance.author.remote_id, 232760293)
        self.assertTrue(len(instance.text) > 10)
        self.assertIsNotNone(instance.date)

    def test_comment_crud_methods(self):
        group = GroupFactory(remote_id=GROUP_CRUD_ID)
        album = AlbumFactory(remote_id=ALBUM_CRUD_ID, group=group)
        photo = PhotoFactory(remote_id=PHOTO_CRUD_ID, group=group, album=album)

        def assert_local_equal_to_remote(comment):
            comment_remote = Comment.remote.fetch_photo(photo=comment.photo).get(remote_id=comment.remote_id)
            self.assertEqual(comment_remote.remote_id, comment.remote_id)
            self.assertEqual(comment_remote.text, comment.text)
            self.assertEqual(comment_remote.author, comment.author)

        Comment.remote.fetch_photo(photo=photo)
        self.assertEqual(Comment.objects.count(), 0)

        # create
        comment = Comment(text='Test comment', photo=photo, author=group, date=datetime.now())
        comment.save(commit_remote=True)
        self.objects_to_delete += [comment]

        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.author, group)
        self.assertNotEqual(len(comment.remote_id), 0)
        assert_local_equal_to_remote(comment)

        # create by manager
        comment = Comment.objects.create(text='Test comment created by manager', photo=photo, author=group, date=datetime.now(), commit_remote=True)
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
        self.assertEqual(Comment.remote.fetch_photo(photo=comment.photo).filter(remote_id=comment.remote_id).count(), 0)

        # restore
        comment.restore(commit_remote=True)
        self.assertFalse(comment.archived)

        self.assertEqual(Comment.objects.count(), 2)
        assert_local_equal_to_remote(comment)
