# -*- coding: utf-8 -*-
from annoying.decorators import signals
from models import Photo

#@signals.post_save(sender=Photo)
#def update_photo_counters(sender, instance, created, **kwargs):
#    instance.update_likes()
#    instance.fetch_comments()