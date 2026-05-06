# TwitterX Py Lib

封装 Twitter/X 用户媒体资源检索与下载的 Python 库，调用简单，仅需几行代码即可快速开始。

## 快速开始

```python
from twitterxlib import TwitterXClient

# 初始化客户端（填入浏览器的 auth_token 和 ct0）
client = TwitterXClient("auth_token=xxx; ct0=xxx;")

# 一键下载该用户发布的所有图片/视频到本地
client.download_user_media_by_name("username", "./download")
```

## 安装

```bash
pip install -r requirements.txt
```

## 高级用法

支持按日期范围过滤、是否包含视频等自定义配置：

```python
config = {
    'start_date': '2023-01-01',
    'end_date': '2024-12-31',
    'has_video': True
}
source_list = client.get_user_media_by_name("username", config=config)
```

## 项目结构

```
twitterxlib/
├── twitterx_api.py      # API 客户端（对外接口）
├── twitterx_user.py     # 用户数据模型
├── twitterx_source.py   # 媒体资源数据模型
├── network_utils.py     # 网络请求封装
└── network_downloader.py # 下载器
```

## 依赖

- Python >= 3.10
- aiohttp
