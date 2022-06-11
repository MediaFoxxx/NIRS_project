import time
import telebot
import json
from func_api import VkWall
from settings import Settings
from threading import Thread


settings = Settings()
bot = telebot.TeleBot(settings.bot_token)


@bot.message_handler(commands=["start"])
def start_bot(message):
    """Запуск всех функций бота."""

    Thread(target=send_messages, args=(message,)).start()
    Thread(target=check_delete_messages, args=(message,)).start()
    Thread(target=edit_messages, args=(message,)).start()
    Thread(target=clean_data, args=(message,)).start()


@bot.message_handler(commands=["delete"])
def check_delete_messages(message):
    """Проверка на удаление постов со стены группы."""

    VkWall.time_print("'Check and delete messages' function started!")
    while int(time.strftime("%M", time.localtime())) not in range(10, 21):
        time.sleep(600)
    while True:
        try:
            wall = VkWall()
            tf = True

            with open("data/last_posts.json", "r") as f:
                last_posts = json.load(f)

            for post_id in list(reversed(wall.all_posts))[:settings.count_checking_deleted_posts]:
                if post_id not in last_posts:
                    tf = False
                    VkWall.time_print(f'{wall.all_posts[post_id]} was deleted!')
                    for mes in wall.all_posts[post_id]:
                        if mes != 'time':
                            bot.delete_message(chat_id=settings.chat_id, message_id=wall.all_posts[post_id][mes])
                    del wall.all_posts[post_id]
                    del wall.all_posts_text[post_id]

            if tf:
                VkWall.time_print("Nothing to delete.")
            else:
                VkWall.save_json(wall.all_posts, 'all_posts', is_sorted=True)
                VkWall.save_json(wall.all_posts_text, 'all_posts_text', is_sorted=True)

        except Exception as ex:
            VkWall.time_print(ex)
        finally:
            time.sleep(3600 - int(time.time()) % 3600 + 13*60)


@bot.message_handler(commands=["update_messages"])
def send_messages(message):
    """Добавление новых постов из вк."""

    VkWall.time_print("'Send messages' function started!")
    while time.strftime("%M", time.localtime())[-1] not in ('0', '5'):
        time.sleep(60)
    while True:
        try:
            wall = VkWall()
            fixed = wall.get_last_posts()

            # Открепляем пост, если он больше не закреплен
            if not fixed:
                wall.unpin_message(bot)

            with open("data/new_posts.json", 'r', encoding="utf-8") as f:
                new_posts = json.load(f)

            if len(new_posts) == 0:
                VkWall.time_print("No new posts")
            else:
                # Добавление новых записей
                VkWall.time_print("New posts has been prepared!")

                try:
                    for post_id in new_posts.keys():
                        post_text = new_posts[post_id]["wall_post_text"]
                        post_photo = new_posts[post_id]["wall_post_photo"]
                        post_audio = new_posts[post_id]["wall_post_audio"]
                        post_doc = new_posts[post_id]["wall_post_doc"]
                        wall.all_posts[post_id] = {}

                        if post_photo is not None:
                            with open(f"data/photo/{post_id}_photo.jpg", "rb") as f:
                                photo = f.read()
                            if len(post_text) > 1024:
                                wall.all_posts[post_id]['photo'] = bot.send_photo(settings.chat_id,
                                                                                  photo=photo).message_id
                                wall.all_posts[post_id]['text'] = bot.send_message(settings.chat_id,
                                                                                   text=post_text, parse_mode="HTML",
                                                                                   disable_web_page_preview=False,
                                                                                   reply_to_message_id=
                                                                                   wall.all_posts[post_id]
                                                                                   ['photo']).message_id
                            else:
                                wall.all_posts[post_id]['text'] = bot.send_photo(settings.chat_id, photo=photo,
                                                                                 caption=post_text,
                                                                                 parse_mode="HTML").message_id
                        else:
                            wall.all_posts[post_id]['text'] = bot.send_message(settings.chat_id, text=post_text,
                                                                               parse_mode="HTML",
                                                                               disable_web_page_preview=
                                                                               False).message_id

                        if post_audio is not None:
                            with open(f"data/audio/{post_id}_audio.mp3", "rb") as f:
                                audio = f.read()
                            wall.all_posts[post_id]['audio'] = bot.send_audio(settings.chat_id, audio=audio,
                                                                              title=post_audio, reply_to_message_id=
                                                                              wall.all_posts[post_id]
                                                                              ['text']).message_id

                        if post_doc is not None:
                            with open(f"data/docs/{post_id}_{post_doc}", "rb") as f:
                                document = f.read()
                            wall.all_posts[post_id]['doc'] = bot.send_document(settings.chat_id,
                                                                               document=document, reply_to_message_id=
                                                                               wall.all_posts[post_id]['text'],
                                                                               visible_file_name=post_doc).message_id

                        if new_posts[post_id]["Fixed"]:
                            # Проверить еще есть ли закрепление и удалить закрепление
                            wall.unpin_message(bot)
                            bot.pin_chat_message(settings.chat_id, message_id=wall.all_posts[post_id]['text'],
                                                 disable_notification=True)

                        wall.all_posts[post_id]['time'] = int(time.time())
                        time.sleep(10)

                    VkWall.time_print('Posts were updated completely!')
                except Exception as ex:
                    VkWall.time_print(ex)
                finally:
                    VkWall.save_json(wall.all_posts, 'all_posts', is_sorted=True)
                    VkWall.save_json(wall.all_posts_text, 'all_posts_text', is_sorted=True)

        except Exception as ex:
            VkWall.time_print(ex)
        finally:
            time.sleep(300 - int(time.time()) % 300)


@bot.message_handler(commands=["edit"])
def edit_messages(message):
    """Проверяет редактирование постов за последние 24ч"""

    VkWall.time_print("'Check and edit messages' function started!")
    while int(time.strftime("%M", time.localtime())) not in range(21, 31):
        time.sleep(600)
    while True:
        try:
            wall = VkWall()
            tf = True

            for mes in reversed(wall.all_posts):
                if int(time.time()) - wall.all_posts[mes]['time'] > settings.edit_time:
                    break

                post = wall.vk.wall.getById(posts=f'{settings.group_id}_{mes}')
                if post[0]['text'] != wall.all_posts_text[mes]:
                    tf = False
                    new_text = wall.make_text_for_message(post[0])
                    bot.edit_message_text(chat_id=settings.chat_id, message_id=wall.all_posts[mes], text=new_text,
                                          parse_mode='HTML', disable_web_page_preview=False)
                    VkWall.time_print(f'{mes} post has been edited.')
            if tf:
                VkWall.time_print('Nothing to edit.')

        except Exception as ex:
            VkWall.time_print(ex)
        finally:
            time.sleep(3600 - int(time.time()) % 3600 + 23*60)


@bot.message_handler(commands=["clean"])
def clean_data(message):
    """Отчищаем файлы."""

    VkWall.time_print("'Clean data' function started!")
    while time.strftime("%H", time.localtime()) != '00':
        time.sleep(3600)
    while True:
        try:
            wall = VkWall()

            wall.clean_directory('audio')
            wall.clean_directory('docs')
            wall.clean_directory('photo')

            if len(wall.all_posts_text) > settings.count_safe_posts:
                num = 0
                apt_d = list(wall.all_posts_text)
                for key in apt_d:
                    if num < len(apt_d) - settings.count_safe_posts:
                        del wall.all_posts[key]
                        del wall.all_posts_text[key]
                    else:
                        break
                    num += 1

                VkWall.save_json(wall.all_posts, 'all_posts', is_sorted=True)
                VkWall.save_json(wall.all_posts_text, 'all_posts_text', is_sorted=True)
            VkWall.time_print("'Clean data' function has been completed successfully!")

        except Exception as ex:
            VkWall.time_print(ex)
        finally:
            time.sleep(3600*24 - int(time.time()) % 3600 + 3*60)


def telegram_bot_polling():
    try:
        bot.polling(none_stop=True, timeout=123)
    except Exception as ex:
        VkWall.time_print(ex)
        bot.stop_polling()
        time.sleep(300)
        telegram_bot_polling()


if __name__ == '__main__':
    telegram_bot_polling()
