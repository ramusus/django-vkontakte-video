from django.utils import timezone
import random
import factory

#from vkontakte_groups.factories import GroupFactory
#from vkontakte_users.factories import UserFactory

from . models import Album, Video


class AlbumFactory(factory.DjangoModelFactory):

    remote_id = factory.LazyAttributeSequence(lambda o, n: n)

    videos_count = 0

    class Meta:
        model = Album


class VideoFactory(factory.DjangoModelFactory):

    remote_id = factory.LazyAttributeSequence(lambda o, n: n)
    album = factory.SubFactory(AlbumFactory)

    duration = 0

    date = timezone.now()

    class Meta:
        model = Video
