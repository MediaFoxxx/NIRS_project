from config import *


class Settings:
    """Класс для хранения всех настроек бота."""

    def __init__(self):
        """Инициализирует статические настройки игры."""

        self.group_domain = group_domain    # group name from vk
        self.group_id = group_id    # -........
        self.chat_id = chat_id  # group name from telegram
        self.bot_token = bot_token
        self.vk_token = vk_token
        self.headers = headers

        self.edit_time = 1435 * 60
        self.count_last_posts = 30      # 30 для обычной работы
        self.count_safe_posts = 50
        self.count_checking_deleted_posts = 20
