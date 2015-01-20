import random

from django.utils import timezone
import factory

from . models import Album, Video


class AlbumFactory(factory.DjangoModelFactory):

    remote_id = factory.LazyAttributeSequence(lambda o, n: n)

    videos_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))

    class Meta:
        model = Album


class VideoFactory(factory.DjangoModelFactory):

    remote_id = factory.LazyAttributeSequence(lambda o, n: n)
    album = factory.SubFactory(AlbumFactory)

    duration = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    likes_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    comments_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))

    date = factory.LazyAttribute(lambda o: timezone.now())

    class Meta:
        model = Video
