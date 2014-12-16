Django Vkontakte Video
======================

[![PyPI version](https://badge.fury.io/py/django-vkontakte-video.png)](http://badge.fury.io/py/django-vkontakte-video) [![Build Status](https://travis-ci.org/ramusus/django-vkontakte-video.png?branch=master)](https://travis-ci.org/ramusus/django-vkontakte-video) [![Coverage Status](https://coveralls.io/repos/ramusus/django-vkontakte-video/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-vkontakte-video)

Приложение позволяет взаимодействовать с видео контентом Вконтакте используя стандартные модели Django через Вконтакте API

Установка
---------

    pip install django-vkontakte-video

В `settings.py` необходимо добавить:

    INSTALLED_APPS = (
        ...
        'oauth_tokens',
        'taggit',
        'vkontakte_api',
        'vkontakte_places',
        'vkontakte_groups',
        'vkontakte_users',
        'vkontakte_video',
    )

    # oauth-tokens settings
    OAUTH_TOKENS_HISTORY = True                                         # to keep in DB expired access tokens
    OAUTH_TOKENS_VKONTAKTE_CLIENT_ID = ''                               # application ID
    OAUTH_TOKENS_VKONTAKTE_CLIENT_SECRET = ''                           # application secret key
    OAUTH_TOKENS_VKONTAKTE_SCOPE = ['ads,wall,video,friends,stats']    # application scopes
    OAUTH_TOKENS_VKONTAKTE_USERNAME = ''                                # user login
    OAUTH_TOKENS_VKONTAKTE_PASSWORD = ''                                # user password
    OAUTH_TOKENS_VKONTAKTE_PHONE_END = ''                               # last 4 digits of user mobile phone

Покрытие методов API
--------------------
* [video.getAlbums](https://vk.com/dev/video.getAlbums) – Возвращает список альбомов видеозаписей пользователя или сообщества.
* [video.get](https://vk.com/dev/video.get) – Возвращает информацию о видеозаписях.
* [video.getComments](https://vk.com/dev/video.getComments) – Возвращает список комментариев к видеозаписи.

Примеры использования
---------------------

### Получение видеольбомов

Для этого необходимо установить дополнительно приложение
[`django-vkontakte-groups`](http://github.com/ramusus/django-vkontakte-groups/) и добавить его в `INSTALLED_APPS`

    >>> from vkontakte_groups.models import Group
    >>> from vkontakte_video.models import VideoAlbum
    >>>
    >>> group = Group.remote.fetch(ids=[16297716])[0]
    >>> VideoAlbum.remote.fetch(group=group)
    [<VideoAlbum: Coca-Cola Football>,
    <VideoAlbum: Эстафета Олимпийского огня "Сочи 2014">,
    <VideoAlbum: Олимпиада>...]

Ведеоальбомы группы доступны через менеджер

    >>> group.video_albums.count()
    7

Видезаписи всех альбомов группы доступны через менеджер

    >>> group.videos.count()
    9

### Получение видоезаписей альбома группы через менеджер
    >>> from vkontakte_groups.models import Group
    >>> from vkontakte_video.models import VideoAlbum, Video
    >>>
    >>> group = Group.remote.fetch(ids=[16297716])[0]
    >>> video_album = VideoAlbum.remote.fetch(group=group)[0]
    >>> video_album.fetch_videos()
    [<Video: БРРРАЗИЛИЯ ОТВЕТИТ 08: Финал ЧМ | Картавый футбол + Coca-Cola>,
    <Video: БРРРАЗИЛИЯ ОТВЕТИТ 07: Какая боль! Народ в шоке | Картавый футбол + Coca-Cola>,
    ...]
