# -*- coding: utf-8 -*-
from datetime import datetime
from vkontakte_api.parser import VkontakteParser, VkontakteParseError
import re

class VkontaktePhotosParser(VkontakteParser):
    pass
#    def parse_container_date(self, container):
#
#        text = container.find('span', {'class': re.compile('^rel_date')})
#        if text:
#            text = text.text
#        else:
#            raise VkontakteParseError("Impossible to find date container in %s" % container)
#            return datetime(1970,1,1)
#
#        return self.parse_date(text)

#    def parse_comment(self, content, wall_owner=None):
#        from models import Comment
#        from vkontakte_users.models import User
#
#        remote_id = content['id'][4:]
#        try:
#            instance = Comment.objects.get(remote_id=remote_id)
#        except Comment.DoesNotExist:
#            instance = Comment(remote_id=remote_id)
#
#        comment_text = content.find('div', {'class': 'fw_reply_text'})
#        if comment_text:
#            instance.text = comment_text.text
#
#        # date
#        instance.date = self.parse_container_date(content)
#        # likes
#        instance.likes = self.parse_container_likes(content, 'like_count fl_l')
#
#        # author
#        users = content.findAll('a', {'class': 'fw_reply_author'})
#        slug = users[0]['href'][1:]
#        if wall_owner and wall_owner.screen_name == slug:
#            instance.author = wall_owner
#        else:
#            avatar = content.find('a', {'class': 'fw_reply_thumb'}).find('img')['src']
#            name_parts = users[0].text.split(' ')
#
#            user = User.remote.get_by_slug(slug)
#            if user:
#                user.first_name = name_parts[0]
#                if len(name_parts) > 1:
#                    user.last_name = name_parts[1]
#                user.photo = avatar
#                user.save()
#                instance.author = user
#
#        if len(users) == 2:
#            # this comment is answer
#            slug = users[1]['href'][1:]
#            if wall_owner and wall_owner.screen_name == slug:
#                instance.reply_for = wall_owner
#            else:
#                instance.reply_for = User.remote.get_by_slug(slug)
#                # имя в падеже, аватара нет
#                # чтобы получть текст и ID родительского коммента нужно отправить:
#                #http://vk.com/al_wall.php
#                #act:post_tt
#                #al:1
#                #post:-16297716_126263
#                #reply:1
#
#        instance.fetched = datetime.now()
#        return instance