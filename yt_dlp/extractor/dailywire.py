# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    traverse_obj, parse_iso8601, unified_strdate, try_get,
)


class DailyWireIE(InfoExtractor):
    _VALID_URL = r'https?://www\.dailywire\.com/episode/(?P<id>[^/]+)'
    IE_NAME = 'dailywire'
    IE_DESC = 'dailywire.com'
    _TESTS = [{
        'url': 'https://www.dailywire.com/episode/1-fauci',
        'md5': '27676793d2289f185f6570151c1bc85e',
        'info_dict': {
            'id': '1-fauci',
            'ext': 'mp4',
            'title': '1. Fauci',
            'description': 'md5:9df630347ef85081b7e97dd30bc22853',
            'thumbnail': r're:^https?://.+\.jpg',
            'timestamp': 1645182003,
            'uploader': 'Caroline Roberts',
            'upload_date': '20220325',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        next_data = self._search_nextjs_data(webpage, video_id)
        episode_info = traverse_obj(next_data, ('props', 'pageProps', 'episodeData', 'episode'), default={})

        segments = episode_info.get('segments') or []
        formats, subtitles = [], {}
        for seg in segments:
            if not seg:
                continue
            m3u8_url = seg.get('video')
            fmts, sub = self._extract_m3u8_formats_and_subtitles(m3u8_url, video_id)
            formats.extend(fmts)
            self._merge_subtitles(sub, target=subtitles)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': episode_info.get('title'),
            'description': episode_info.get('description'),
            'thumbnail': episode_info.get('image'),
            'upload_date': unified_strdate(episode_info.get('updatedAt')),
            'timestamp': parse_iso8601(episode_info.get('createdAt')),
            'uploader': f'{try_get(episode_info, lambda x: x["createdBy"]["firstName"])} {try_get(episode_info, lambda x: x["createdBy"]["lastName"])}',
            'formats': formats,
            'subtitles': subtitles,
        }
