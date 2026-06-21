
from typing import List
from .network_utils import NetworkUtils
from .twitterx_user import TwitterXUser
from .twitterx_source import TwitterXSource

class TwitterXClient:
    """
    Twitter/X API 客户端，封装了用户信息查询、媒体资源检索与下载功能。
    """

    def __init__(self, user_token: str):
        """
        初始化 API 客户端。

        :param user_token: Cookie 字符串，需包含 auth_token 与 ct0 字段，
                           格式: "auth_token=xxx; ct0=xxx;"
        """
        self.network = NetworkUtils(user_token)
        self.cache_user_dict = {}
        return

    def get_user_by_name(self, screen_name: str) -> TwitterXUser | None:
        """
        根据用户名查询用户信息（带缓存）。

        :param screen_name: Twitter/X 用户名（@ 后面的字符）
        :return: TwitterXUser 对象，若未找到则返回 None
        """
        if not screen_name or screen_name == "":
            return None
        if screen_name in self.cache_user_dict:
            return self.cache_user_dict[screen_name]

        user_info_dict = self.network.get_user_by_screen_name(screen_name)
        if not user_info_dict:
            return None
        user = TwitterXUser(screen_name, user_info_dict)
        self.cache_user_dict[screen_name] = user

        return user

    def get_user_media_by_name(self, screen_name:str, config: dict = None, is_reset: bool = True) -> list | None:
        """
        获取指定用户发布的所有媒体资源列表。

        :param screen_name: Twitter/X 用户名（@ 后面的字符）
        :param config: 可选检索配置字典，支持的 key:
                       start_date (str) - 起始日期 "YYYY-MM-DD"，默认 "2020-01-01"
                       end_date   (str) - 结束日期 "YYYY-MM-DD"，默认 "2030-01-01"
                       has_video  (bool) - 是否包含视频，默认 False
        :param is_reset: 是否重置之前加载的数据，默认 True
        :return: TwitterXSource 对象列表，失败时返回 None
        """
        user = self.get_user_by_name(screen_name)
        if not user:
            return None

        if not self.load_user_media(user, config, is_reset):
            return None

        return user.source_list

    def get_user_retweet_by_name(self, screen_name:str, config: dict = None, is_reset: bool = True) -> list | None:
        """
        获取指定用户发布的转推资源列表。

        :param screen_name: Twitter/X 用户名（@ 后面的字符）
        :param config: 可选检索配置字典，支持的 key:
                       start_date (str) - 起始日期 "YYYY-MM-DD"，默认 "2020-01-01"
                       end_date   (str) - 结束日期 "YYYY-MM-DD"，默认 "2030-01-01"
                       has_video  (bool) - 是否包含视频，默认 False
        :param is_reset: 是否重置之前加载的数据，默认 True
        :return: TwitterXSource 对象列表，失败时返回 None
        """
        user = self.get_user_by_name(screen_name)
        if not user:
            return None

        if not self.load_user_retweet(user, config, is_reset):
            return None

        return user.retweet_source_list

    def load_user_media(self, user: TwitterXUser, config: dict = None, is_reset: bool = True) -> bool:
        """
        加载指定用户的所有媒体资源（分页拉取）。

        :param user: TwitterXUser 对象
        :param config: 检索配置，同 get_user_media_by_name 中的 config
        :param is_reset: 是否重置之前加载的数据
        :return: 成功返回 True，失败返回 False
        """
        if not user:
            return False

        if is_reset:
            user.reset_data()

        failed_count = 0
        while user.is_continue_loading():
            if failed_count >= 5:
                return False

            media_dict = self.network.get_user_media(user.rest_id, user.cursor)
            if not media_dict:
                print('No media found')
                failed_count += 1
                continue
            if not config:
                config = {}
            if user.load_media_dict(media_dict, config):
                failed_count = 0
            else:
                print('Failed to load media for ' + user.print_user_info())
                failed_count += 1
                continue

        return True

    def load_user_retweet(self, user: TwitterXUser, config: dict = None, is_reset: bool = True) -> bool:
        """
        加载指定用户的转贴（分页拉取）。

        :param user: TwitterXUser 对象
        :param config: 检索配置，同 get_user_media_by_name 中的 config
        :param is_reset: 是否重置之前加载的数据
        :return: 成功返回 True，失败返回 False
        """
        if not user:
            return False

        if is_reset:
            user.reset_data()

        failed_count = 0
        while user.is_continue_loading():
            if failed_count >= 5:
                return False

            media_dict = self.network.get_user_retweet(user.rest_id, user.cursor)
            if not media_dict:
                print('No media found')
                failed_count += 1
                continue
            if not config:
                config = {}
            if user.load_retweet_dict(media_dict, config, config.get('is_load_retweet_source', True)):
                failed_count = 0
            else:
                print('Failed to load media for ' + user.print_user_info())
                failed_count += 1
                continue

        return True

    def download_user_media_by_name(self, screen_name: str, download_path: str, config: dict = None, is_reset: bool = True) -> bool:
        """
        下载指定用户发布的所有媒体资源到本地。

        :param screen_name: Twitter/X 用户名（@ 后面的字符）
        :param download_path: 本地下载目录路径
        :param config: 检索配置，同 get_user_media_by_name 中的 config
        :param is_reset: 是否重置之前加载的数据
        :return: 全部下载成功返回 True，否则返回 False
        """
        if not screen_name or screen_name == "":
            return False
        if not download_path or download_path == "":
            return False

        download_source_list = self.get_user_media_by_name(screen_name, config, is_reset)
        if not download_source_list:
            return False

        return self.download_source_list(download_source_list, download_path)

    def download_source_list(self, source_list: List[TwitterXSource], download_path: str) -> bool:
        """
        下载指定的媒体资源列表到本地。

        :param source_list: TwitterXSource 对象列表
        :param download_path: 本地下载目录路径
        :return: 全部下载成功返回 True，否则返回 False
        """
        if not download_path or download_path == "":
            return False

        if not source_list or len(source_list) <=0:
            return False

        download_task_list = [item.get_task_dict(download_path) for item in source_list]
        return self.network.download_source_by_list(download_task_list)

    def get_user_retweet_screen_name_list(self, screen_name:str, config: dict = None, is_reset: bool = False) -> list | None:
        """
                获取指定用户转推的用户列表。

                :param screen_name: Twitter/X 用户名（@ 后面的字符）
                :param config: 可选检索配置字典，支持的 key:
                               start_date (str) - 起始日期 "YYYY-MM-DD"，默认 "2020-01-01"
                               end_date   (str) - 结束日期 "YYYY-MM-DD"，默认 "2030-01-01"
                :param is_reset: 是否重置之前加载的数据，默认 True
                :return: TwitterXSource 对象列表，失败时返回 None
                """
        user = self.get_user_by_name(screen_name)
        if not user:
            return None

        if len(user.retweet_screen_name_list) > 0:
            return user.retweet_screen_name_list

        if not config:
            config = {}
        config['is_load_retweet_source'] = False

        if not self.load_user_retweet(user, config, is_reset):
            return None

        return user.retweet_screen_name_list
