# -*- coding: utf-8 -*-
from django.contrib import admin
from django.core.urlresolvers import reverse
from vkontakte_api.admin import VkontakteModelAdmin
from models import VideoAlbum, Video, Comment


class VideoInline(admin.TabularInline):

    def image(self, instance):
        return '<img src="%s" />' % (instance.photo_130,)
    image.short_description = 'video'
    image.allow_tags = True

    model = Video
    fields = ('title', 'image', 'owner', 'comments_count', 'views_count')
    readonly_fields = fields
    extra = False
    can_delete = False


class VideoAlbumAdmin(VkontakteModelAdmin):

    def image_preview(self, obj):
        return u'<a href="%s"><img src="%s" height="30" /></a>' % (obj.link, obj.photo_160)
    image_preview.short_description = u'Картинка'
    image_preview.allow_tags = True

    list_display = ('image_preview', 'remote_id', 'title', 'owner', 'group', 'videos_count')
    list_display_links = ('title', 'remote_id',)
    search_fields = ('title', 'description')
    inlines = [VideoInline]


class VideoAdmin(VkontakteModelAdmin):

    def image_preview(self, obj):
        return u'<a href="%s"><img src="%s" height="30" /></a>' % (obj.link, obj.photo_130)
    image_preview.short_description = u'Картинка'
    image_preview.allow_tags = True
    '''
    def text_with_link(self, obj):
        return u'%s <a href="%s"><strong>ссылка</strong></a>' % (obj.title, )
    text_with_link.short_description = u'Текст'
    text_with_link.allow_tags = True
    '''

    list_display = ('image_preview', 'remote_id', 'title', 'video_album', 'comments_count', 'views_count', 'date')
    list_display_links = ('remote_id', 'title')
    list_filter = ('video_album',)


class CommentAdmin(VkontakteModelAdmin):
    list_display = ('remote_id', 'video', 'author_id', 'text', 'date')
    list_filter = ('video',)


admin.site.register(VideoAlbum, VideoAlbumAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Comment, CommentAdmin)
