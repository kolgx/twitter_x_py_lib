
from twitterxlib import TwitterXClient

USER_TOKEN="auth_token=xxxxxxxxxxx; ct0=xxxxxxxxxxx;"
USER_SCREEN_LIST=['user1', 'user2']

def main():
    # 1. 初始化API客户端
    client = TwitterXClient(USER_TOKEN) # 填入 cookie (auth_token与ct0字段) //重要:替换掉其中的x即可, 注意不要删掉分号

    # 2. 加载目标用户信息（可选）
    user = client.get_user_by_name(USER_SCREEN_LIST[0]) # 填入要下载的用户名(@后面的字符)
    if user:
        user.print_user_info()

    # 3. 获取目标用户发布资源列表，默认2020年-2030年，默认不检索视频
    config = { # 可选，自定义资源检索范围
        'start_date': '2026-05-01',
        'end_date': '2027-01-01',
        'has_video': True # 启用视频检索
    }
    source_list = client.get_user_media_by_name(USER_SCREEN_LIST[0], config=config) # 填入要下载的用户名(@后面的字符)

    # 4. 转换为资源网址列表，便于工作流处理（可选）
    if source_list:
        source_json_list = [item.url for item in source_list]

    # 5. 下载目标用户发布的资源
    if client.download_user_media_by_name(USER_SCREEN_LIST[0], './download/twitter/user1', config=config):
        print(f'success download user[{user.name}] source to local')

    return

if __name__ == '__main__':
    main()

