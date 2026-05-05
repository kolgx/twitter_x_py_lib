
import re
import httpx
import json
from typing import Dict, Any
from .simple_tool_utils import quote_url

class NetworkUtils:
    def __init__(self, cookie: str, network_proxy: str=None):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'cookie': cookie
        }
        re_token = r'ct0=(.*?);'
        tokens = re.findall(re_token, cookie)
        if tokens:
            self.headers['x-csrf-token'] = tokens[0]

        self.proxy = network_proxy
        self.request_count = 0
        return

    def get_user_by_screen_name(self, screen_name: str) -> Dict[str, Any] | None:
        self.headers['referer'] = f'https://twitter.com/{screen_name}'
        url = (
            f'https://twitter.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName'
            f'?variables={{"screen_name":"{screen_name}","withSafetyModeUserFields":false}}'
            f'&features={{"hidden_profile_likes_enabled":false,"hidden_profile_subscriptions_enabled":false,'
            f'"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,'
            f'"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,'
            f'"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,'
            f'"responsive_web_graphql_timeline_navigation_enabled":true}}'
            f'&fieldToggles={{"withAuxiliaryUserLabels":false}}'
        )
        try:
            response = httpx.get(quote_url(url), headers=self.headers, proxy=self.proxy)
            self.request_count += 1
            raw_data = json.loads(response.text)
            return raw_data.get('data', {}).get('user', {}).get('result', None)
        except Exception as e:
            print(f"Failed to get info for {screen_name}: {e}")
            return None

    def get_user_media(self, rest_id: str, cursor: str = None) -> Dict[str, Any] | None:
        url_top = (
            f'https://twitter.com/i/api/graphql/Le6KlbilFmSu-5VltFND-Q/UserMedia'
            f'?variables={{"userId":"{rest_id}","count":500,'
        )
        url_bottom = (
            f'"includePromotedContent":false,"withClientEventToken":false,"withBirdwatchNotes":false,'
            f'"withVoice":true,"withV2Timeline":true}}'
            f'&features={{"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,'
            f'"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,'
            f'"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,'
            f'"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,'
            f'"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,'
            f'"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,'
            f'"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,'
            f'"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,'
            f'"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}}'
        )

        if cursor:
            url = f'{url_top}"cursor":"{cursor}",{url_bottom}'
        else:
            url = f'{url_top}{url_bottom}'

        try:
            response = httpx.get(quote_url(url), headers=self.headers, proxy=self.proxy)
            self.request_count += 1
            if response.status_code == 429:
                print('API Rate limit exceeded')
                return None
            return json.loads(response.text)
        except Exception as e:
            print(f'Failed to fetch user media: {e}')
            return None