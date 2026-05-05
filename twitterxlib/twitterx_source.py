
from .simple_tool_utils import *


class TwitterXSource:
    def __init__(self):
        self.url = ''
        self.type = 0 # 0: undefine; 1: image; 2: video
        self.suffix = ''
        self.file_name = ''
        return

    def __str__(self):
        return f"{self.type} | {self.file_name} | {self.suffix}"

    def load(self, source_dict: dict, timestr: str, download_count:int, has_video: bool = False) -> bool:

        if 'video_info' in source_dict and has_video:
            video_url = get_highest_video_quality(source_dict['video_info']['variants'])
            file_name = f"{timestr}-vid_{download_count}"
            self.url = video_url
            self.type = 2
            self.suffix = 'mp4'
            self.file_name = file_name
        elif 'media_url_https' in source_dict:
            img_url = source_dict['media_url_https']
            file_name = f"{timestr}-img_{download_count}"
            self.url = img_url
            self.type = 2
            self.suffix = img_url[-3:]
            self.file_name = file_name
        else:
            return False
        return True