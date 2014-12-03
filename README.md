Django Vkontakte Videos
=======================

[![PyPI version](https://badge.fury.io/py/django-vkontakte-videos.png)](http://badge.fury.io/py/django-vkontakte-videos) [![Build Status](https://travis-ci.org/ramusus/django-vkontakte-videos.png?branch=master)](https://travis-ci.org/ramusus/django-vkontakte-videos) [![Coverage Status](https://coveralls.io/repos/ramusus/django-vkontakte-videos/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-vkontakte-videos)

Приложение позволяет взаимодействовать с видео контентом Вконтакте используя стандартные модели Django через Вконтакте API

Установка
---------

    pip install django-vkontakte-videos

В `settings.py` необходимо добавить:

    INSTALLED_APPS = (
        ...
        'oauth_tokens',
        'taggit',
        'vkontakte_api',
        'vkontakte_places,
        'vkontakte_groups',
        'vkontakte_users',
        'vkontakte_videos',
    )

    # oauth-tokens settings
    OAUTH_TOKENS_HISTORY = True                                         # to keep in DB expired access tokens
    OAUTH_TOKENS_VKONTAKTE_CLIENT_ID = ''                               # application ID
    OAUTH_TOKENS_VKONTAKTE_CLIENT_SECRET = ''                           # application secret key
    OAUTH_TOKENS_VKONTAKTE_SCOPE = ['ads,wall,videos,friends,stats']    # application scopes
    OAUTH_TOKENS_VKONTAKTE_USERNAME = ''                                # user login
    OAUTH_TOKENS_VKONTAKTE_PASSWORD = ''                                # user password
    OAUTH_TOKENS_VKONTAKTE_PHONE_END = ''                               # last 4 digits of user mobile phone

Покрытие методов API
--------------------

* [photos.getAlbums](http://vk.com/dev/photos.getAlbums) – возвращает список альбомов пользователя;
...

В планах:

...

Использование парсера
---------------------

* Получение количества комментариев к фотографии; *
* Получение количества лайков фотографии; *

(*) Дублирование функционала API

Примеры использования
---------------------

### Получение фотоальбомов группы через метод группы

Для этого необходимо установить дополнительно приложение
[`django-vkontakte-groups`](http://github.com/ramusus/django-vkontakte-groups/) и добавить его в `INSTALLED_APPS`

    >>> from vkontakte_groups.models import Group
    >>> group = Group.remote.fetch(ids=[16297716])[0]
    >>> group.fetch_albums()
    [<Album: Coca-Cola привозила кубок мира по футболу FIFA>,
     <Album: Старая реклама Coca-Cola>,
     '...(remaining elements truncated)...']

Фотоальбомы группы доступны через менеджер

    >>> group.photo_albums.count()
    47

Фотографии всех альбомов группы доступны через менеджер

    >>> group.photos.count()
    4432

### Получение фотоальбомов группы через менеджер

    >>> from vkontakte_groups.models import Group
    >>> from vkontakte_photos.models import Album
    >>> group = Group.remote.fetch(ids=[16297716])[0]
    >>> Album.remote.fetch(group=group, ids=[106769855])
    [<Album: Coca-Cola привозила кубок мира по футболу FIFA>]

### Получение фотографий альбома пользователя через менеджер

Для этого необходимо установить дополнительно приложение
[`django-vkontakte-users`](http://github.com/ramusus/django-vkontakte-users/) и добавить его в `INSTALLED_APPS`

    >>> from vkontakte_users.models import User
    >>> from vkontakte_photos.models import Album, Photo
    >>> user = User.remote.fetch(ids=[1])[0]
    >>> album = Album.remote.fetch(user=user, ids=[159337866])[0]
    >>> Photo.remote.fetch(album=album)
    [<Photo: Photo object>,
     <Photo: Photo object>,
     <Photo: Photo object>,
     <Photo: Photo object>]
