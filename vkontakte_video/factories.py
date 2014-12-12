from datetime import datetime
import random

import factory
from vkontakte_groups.factories import GroupFactory
from vkontakte_users.factories import UserFactory

from models import VideoAlbum, Video


class AlbumFactory(factory.DjangoModelFactory):

    remote_id = factory.LazyAttributeSequence(lambda o, n: n)

    owner = factory.SubFactory(UserFactory)
    group = factory.SubFactory(GroupFactory)

    videos_count = 0

    class Meta:
        model = VideoAlbum


class VideoFactory(factory.DjangoModelFactory):

    remote_id = factory.LazyAttributeSequence(lambda o, n: n)
    video_album = factory.SubFactory(AlbumFactory)

    owner = factory.SubFactory(UserFactory)
    group = factory.SubFactory(GroupFactory)

    duration = 0

    date = datetime.now()

    class Meta:
        model = Video
