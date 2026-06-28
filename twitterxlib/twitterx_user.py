
from .simple_tool_utils import *
from .twitterx_source import TwitterXSource

class TwitterXUser:
    def __init__(self, screen_name: str, user_info_dict: dict):
        self.screen_name = screen_name
        self._user_info_dict = user_info_dict
        self.rest_id = user_info_dict.get('rest_id', '')
        self.name = user_info_dict.get('legacy', {}).get('name')
        self.statuses_count = user_info_dict.get('legacy', {}).get('statuses_count')
        self.media_count = user_info_dict.get('legacy', {}).get('media_count', 0)

        self.cursor = None
        self.start_label = True
        self.first_page = True
        self.download_count = 0
        self.retweet_download_count = 0
        self.has_next_page = True
        self.source_list = []
        self.retweet_source_list = []
        self.retweet_screen_name_list = []
        return

    def __str__(self):
        return f'{self.screen_name} | {self.name} | {self.media_count} | {len(self.source_list)}'

    def print_user_info(self):
        print(f"昵称:{self.name}")
        print(f"用户名:{self.screen_name}")
        print(f"数字ID:{self.rest_id}")
        print(f"媒体推数:{self.media_count}")
        return

    def is_continue_loading(self):
        return self.start_label and self.has_next_page

    def reset_data(self):
        self.cursor = None
        self.start_label = True
        self.first_page = True
        self.download_count = 0
        self.retweet_download_count = 0
        self.has_next_page = True
        self.source_list = []
        self.retweet_source_list = []
        self.retweet_screen_name_list = []
        return

    def load_media_dict(self, media_dict: dict, config: dict) -> bool:
        if not media_dict:
            return False
        try:
            raw_instructions = media_dict['data']['user']['result']['timeline_v2']['timeline']['instructions']
        except KeyError:
            print("API响应中未找到 timeline_v2 结构")
            return False

        # 更新指针位置
        next_cursor = None
        for instr in raw_instructions:
            if 'entries' in instr:
                for i in instr['entries']:
                    if 'bottom' in i['entryId']:
                        next_cursor = i['content']['value']
        self.cursor = next_cursor

        # 定位推文内容
        raw_data = []
        if self.first_page:
            try:
                # 寻找含有entries并且不是光标的指令
                entries_instr = next((instr for instr in raw_instructions if instr.get('type') == 'TimelineAddEntries'), {'entries': []})
                if entries_instr:
                    for entry in entries_instr['entries']:
                        raw_data = entry.get('content', {}).get('items', [])
                        if raw_data and len(raw_data) > 0:
                            break
                self.first_page = False
            except Exception as e:
                print(f"解析第一页数据结构发生错误: {e}")
                self.has_next_page = False
        else:
            module_items_instr = next( (instr for instr in raw_instructions if instr.get('type') == 'TimelineAddToModule'), {})
            if not module_items_instr or 'moduleItems' not in module_items_instr:
                self.has_next_page = False
            else:
                raw_data = module_items_instr['moduleItems']

        if not raw_data or len(raw_data) == 0:
            print(f"定位推文内容失败")
            self.has_next_page = False
            return False

        # 解析推文内容
        for item in raw_data:
            try:
                if 'promoted-tweet' in item['entryId']:
                    continue
                if 'tweet' in item['entryId']:
                    source_dict = item['item']['itemContent']['tweet_results']['result']
                else:
                    continue

                if 'tweet' in source_dict:
                    legacy = source_dict['tweet']['legacy']
                    tweet_msecs = int(source_dict['tweet']['edit_control']['editable_until_msecs']) - 3600000
                else:
                    legacy = source_dict['legacy']
                    if 'editable_until_msecs' in source_dict['edit_control']:
                        tweet_msecs = int(source_dict['edit_control']['editable_until_msecs']) - 3600000
                    else:
                        tweet_msecs = int(source_dict['edit_control']['edit_control_initial']['editable_until_msecs']) - 3600000

                timestr = stamp2time(tweet_msecs)
                _result = time_comparison(timestr, config.get('start_date', '2020-01-01'), config.get('end_date', '2030-01-01'))

                if not _result[0]:  # 不符合时间限制
                    if not _result[1]:
                        self.start_label = False
                        break
                    continue

                if 'retweeted_status_result' in legacy:  # 排除转推
                    continue

                if not 'extended_entities' in legacy:
                    continue

                for _media in legacy['extended_entities']['media']:
                    source = TwitterXSource()
                    if source.load(_media, timestr, self.download_count, config.get('has_video', False)):
                        self.source_list.append(source)
                        self.download_count += 1
            except Exception as e:
                print(f"解析单条出现的异常: {e}")
                pass
        return True

    def load_retweet_dict(self, retweet_dict: dict, config: dict, is_load_retweet_source:bool = True) -> bool:
        if not retweet_dict:
            return False
        try:
            raw_data = retweet_dict['data']['user']['result']['timeline_v2']['timeline']['instructions'][-1]['entries']
        except KeyError:
            print("API响应中未找到 timeline_v2 结构")
            return False

        # 解析推文内容
        for item in raw_data:
            try:
                if 'cursor-bottom' in item['entryId']:  # 更新下一页的请求编号(含转推模式&亮点模式)
                    self.cursor = item['content']['value']
                    continue
                if 'tweet' in item['entryId']:
                    source_dict = item['content']['itemContent']['tweet_results']['result']
                else:
                    continue

                if 'tweet' in source_dict:
                    legacy = source_dict['tweet']['legacy']
                    tweet_msecs = int(source_dict['tweet']['edit_control']['editable_until_msecs']) - 3600000
                else:
                    legacy = source_dict['legacy']
                    tweet_msecs = int(source_dict['edit_control']['editable_until_msecs']) - 3600000

                timestr = stamp2time(tweet_msecs) #此时间是转贴时间
                _result = time_comparison(timestr, config.get('start_date', '2020-01-01'), config.get('end_date', '2030-01-01'))

                if not _result[0]:  # 不符合时间限制
                    if not _result[1]:
                        self.start_label = False
                        break
                    continue

                if not 'retweeted_status_result' in legacy:  # 只要转推
                    continue

                tmp_tweet_retweet = legacy['retweeted_status_result']['result']
                if not 'core' in tmp_tweet_retweet:
                    tmp_tweet_retweet = legacy['retweeted_status_result']['result'].get('tweet')
                # name = tmp_tweet_retweet['core']['user_results']['result']['legacy']['name']
                screen_name = tmp_tweet_retweet['core']['user_results']['result']['legacy']['screen_name']
                # full_text = tmp_tweet_retweet['legacy']['full_text']

                if not screen_name in self.retweet_screen_name_list:
                    self.retweet_screen_name_list.append(screen_name)

                if not is_load_retweet_source:
                    continue

                for _media in tmp_tweet_retweet['legacy']['extended_entities']['media']:
                    source = TwitterXSource()
                    if source.load(_media, timestr, self.download_count, config.get('has_video', False)):
                        self.retweet_source_list.append(source)
                        self.retweet_download_count += 1
            except Exception as e:
                print(f"解析单条出现的异常: {e}")
                pass
        return True