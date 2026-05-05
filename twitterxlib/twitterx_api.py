
from typing import List
from .network_utils import NetworkUtils
from .twitterx_user import TwitterXUser
from .twitterx_source import TwitterXSource

class TwitterXClient:
    def __init__(self, user_token: str):
        self.user_token = user_token
        self.network = NetworkUtils(user_token)
        self.cache_user_dict = {}
        return

    def get_user_by_name(self, screen_name: str) -> TwitterXUser | None:
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
        user = self.get_user_by_name(screen_name)
        if not user:
            return None

        if not self.load_user_media(user, config, is_reset):
            return None

        return user.source_list

    def load_user_media(self, user: TwitterXUser, config: dict = None, is_reset: bool = True) -> bool:
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

    def download_user_media_by_name(self, screen_name: str, download_path: str, config: dict = None, is_reset: bool = True) -> bool:
        if not screen_name or screen_name == "":
            return False
        if not download_path or download_path == "":
            return False

        download_source_list = self.get_user_media_by_name(screen_name, config, is_reset)
        if not download_source_list:
            return False
        
        pass

    def download_source_list(self, source_list: List[TwitterXSource]) -> bool:
        pass #TODO: 使用network_downloader.py多线程下载
