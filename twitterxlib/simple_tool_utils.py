import re
import time
from urllib.parse import quote as url_quote
from datetime import datetime
from typing import List, Dict

def quote_url(url: str) -> str:
    if '%' in url:
        return url
    return url_quote(url, safe=':/?&=%#@[]!$()*,;+')

def del_special_char(string: str) -> str:
    string = re.sub(r'[^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a\u3040-\u31FF\.]', '', string)
    return string

def stamp2time(msecs_stamp: int) -> str:
    timeArray = time.localtime(msecs_stamp / 1000)
    return time.strftime("%Y-%m-%d", timeArray)

def time2stamp(timestr: str) -> int:
    datetime_obj = datetime.strptime(timestr, "%Y-%m-%d")
    msecs_stamp = int(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
    return msecs_stamp


def time_comparison(now_str: str, start_str: str, end_str: str) -> List[bool]:
    """
    使用 datetime 对象进行时间范围判定
    :param now_str: 当前条目的发布时间
    :param start_str: 目标时间范围的起点 (较旧的时间)
    :param end_str: 目标时间范围的终点 (较新的时间)
    """
    # 初始化状态
    is_in_range = False  # 是否符合抓取条件
    should_continue = True  # 是否继续向下翻页 (Twitter流是从新到旧)

    now = datetime.strptime(now_str, '%Y-%m-%d')
    start = datetime.strptime(start_str, '%Y-%m-%d')
    end = datetime.strptime(end_str, '%Y-%m-%d')

    # 逻辑判断
    # 假设 Twitter 排序为：[新] -> [旧]
    if start <= now <= end:
        is_in_range = True
    elif now < start:
        # 如果当前帖子时间已经早于我们设定的起始点，说明后面的帖子更旧，可以停止了
        should_continue = False

    return [is_in_range, should_continue]

def get_highest_video_quality(variants: List[Dict]) -> str | None:
    if len(variants) == 1:
        return variants[0]['url']
    
    max_bitrate = 0
    highest_url = None
    for i in variants:
        if 'bitrate' in i:
            if int(i['bitrate']) > max_bitrate:
                max_bitrate = int(i['bitrate'])
                highest_url = i['url']
    return highest_url
