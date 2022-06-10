import vk_api
import json
import requests
import time
import re
import glob
import os
from settings import Settings


class VkWall:
    """Класс поста из вк."""

    def __init__(self):
        """Инициализирует объект класса."""

        self.settings = Settings()
        self._vk_session = vk_api.VkApi(token=self.settings.vk_token)
        self.vk = self._vk_session.get_api()
        self.wall = self.vk.wall.get(domain=self.settings.group_domain, count=self.settings.count_last_posts)["items"]

        with open("data/all_posts.json", "r", encoding="utf-8") as f:
            self.all_posts = json.load(f)
        with open("data/all_posts_text.json", "r", encoding="utf-8") as f:
            self.all_posts_text = json.load(f)

        self.new_posts = {}
        self.last_posts = []

    @staticmethod
    def clean_directory(name='audio'):
        """Отчистка папки от файлов"""

        files = glob.glob(f'/data\\{name}\\*')
        for file in files:
            os.remove(file)

    @staticmethod
    def save_json(json_file, name, is_sorted=False):
        """Функция сохранения json-файла(отсортированного)."""

        if is_sorted:
            with open(f"data/{name}.json", 'w', encoding="utf-8") as f:
                json.dump(dict(sorted(json_file.items(), key=lambda x: int(x[0]))), f, indent=4, ensure_ascii=False)
                # json.dump(json_file, f, indent=4, ensure_ascii=False, sort_keys=True)
        else:
            with open(f"data/{name}.json", 'w', encoding="utf-8") as f:
                json.dump(json_file, f, indent=4, ensure_ascii=False)

    @staticmethod
    def _hidden_links(text):
        """Извлечение из текста ссылок спрятанных в текст."""

        reg = r'\[((id)|(club))\d+\|[^\[\]\|]+\]'
        line = re.search(reg, text)

        while line is not None:
            link = line[0].split('|')
            url = f'<a href="https://vk.com/{link[0][1:]}">{link[1][:-1]}</a>'
            text = text.replace(line[0], url)
            line = re.search(reg, text)

        return text

    def make_text_for_message(self, post):
        """Изменение текста из поста вк для сообщения в телеге"""

        copy_quote_url = ''
        if 'copy_history' in post.keys():
            copy_post = post['copy_history'][0]
            copy_post_group = self.vk.groups.getById(group_id=str(copy_post['owner_id'])[1:])[0]
            copy_quote_url = f"\n\n<a href='https://vk.com/{copy_post_group['screen_name']}?w=wall-" \
                             f"{copy_post_group['id']}_{copy_post['id']}'>{copy_post_group['name']}</a>"

        text = post['text'] + copy_quote_url

        if 'attachments' in post.keys():
            for attach in post['attachments']:
                if attach['type'] == 'link':
                    link = attach['link']
                    link_url = link['url']
                    if link_url not in text:
                        text += f"\n\n<a href='{link_url}'>{link['title']}</a>"

                if attach['type'] == 'video':
                    video = attach['video']
                    video_url = 'https://vk.com/video%r_%r' % (video['owner_id'], video['id'])
                    text += f"\n\n<a href='{video_url}'>{video['title']}</a>"

        text = self._hidden_links(text)
        return text

    def _make_message_from_vkpost(self, post, fixed):
        """Создание макета сообщения для телеграма из поста в вк"""

        self.new_posts[post['id']] = {}
        self.new_posts[post['id']]["Fixed"] = fixed
        self.new_posts[post['id']]["wall_post_photo"] = None
        self.new_posts[post['id']]["wall_post_audio"] = None
        self.new_posts[post['id']]["wall_post_doc"] = None

        if 'attachments' in post.keys():
            for attach in post['attachments']:

                if attach['type'] == 'photo':
                    for photo in attach['photo']['sizes']:
                        if photo['type'] in ('z', 'y', 'x'):
                            self.new_posts[post['id']]["wall_post_photo"] = f'{post["id"]}_photo'

                            photo_jpg = requests.get(url=photo['url'])
                            with open(f'data/photo/{post["id"]}_photo.jpg', 'wb') as f:
                                f.write(photo_jpg.content)

                            break

                if attach['type'] == 'audio' and attach['audio']['url'] != '':
                    audio = attach['audio']
                    self.new_posts[post['id']]["wall_post_audio"] = f"{audio['artist']} - {audio['title']}"

                    audio_mp3 = requests.get(url=audio['url'])
                    with open(f'data/audio/{post["id"]}_audio.mp3', 'wb') as f:
                        f.write(audio_mp3.content)

                if attach['type'] == 'doc':
                    doc = attach['doc']
                    self.new_posts[post['id']]["wall_post_doc"] = doc['title']

                    doc_ext = requests.get(url=doc['url'])
                    with open(f'data/docs/{post["id"]}_{doc["title"]}', 'wb') as f:
                        f.write(doc_ext.content)

        self.new_posts[post['id']]["wall_post_text"] = self.make_text_for_message(post)

    def get_last_posts(self):
        """Получение последних постов со стены группы вк."""

        fixed = False
        if 'is_pinned' in self.wall[0].keys():
            fixed = True

        for post in self.wall:
            if str(post['id']) not in self.all_posts_text.keys():
                self.all_posts_text[post['id']] = post['text']
            self.last_posts.append(str(post['id']))

            if str(post['id']) not in self.all_posts.keys():
                if post == self.wall[0]:
                    self._make_message_from_vkpost(post, fixed)
                else:
                    self._make_message_from_vkpost(post, False)

        self.save_json(self.new_posts, 'new_posts', is_sorted=True)
        self.save_json(self.all_posts_text, 'all_posts_text', is_sorted=True)
        self.save_json(self.last_posts, 'last_posts')

        return fixed

    def unpin_message(self, bot):
        """Открепляем закрепленный пост."""

        try:
            bot.unpin_chat_message(self.settings.chat_id)
            self.time_print('Post was unpinned.')
        except Exception as ex:
            pass
            # self.time_print(ex)

    @staticmethod
    def time_print(text):
        print(f"{time.strftime('%H:%M:%S', time.localtime())} - {text}")
