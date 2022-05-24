class Settings:
    """Класс для хранения всех настроек бота."""

    def __init__(self):
        """Инициализирует статические настройки игры."""

        self.group_domain = 'decanat_rk'
        self.group_id = -56443935
        self.chat_id = "@decanat_rk"
        self.bot_token = "5262146244:AAFELyFupCJ42On-F7eCAmyqxnfiTtIdFr0"
        self.vk_token = "eef85a7cb86c9b19b4b8af03b3d07565e7f9c4707dd4e722463f3008c4aacbc9ff3cd259e690beeb59258"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98"
                          ".0.4758.119 YaBrowser/22.3.0.2430 Yowser/2.5 Safari/537.36"
        }

        self.edit_time = 1435 * 60
        self.count_last_posts = 30      # 30 для обычной работы
        self.count_safe_posts = 50
        self.count_checking_deleted_posts = 20
