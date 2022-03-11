# coding: utf-8
from __future__ import unicode_literals

import base64
import re

from yt_dlp.utils import update_url_query, js_to_json

from .common import InfoExtractor

class QQIE(InfoExtractor):
    IE_DESC = 'qq.com'
    IE_NAME = 'QQ:video'
    TESTS = [{
        'url': 'https://v.qq.com/x/page/o3208rrtzzp.html'
    }]
    _VALID_URL = r'https?://v\.qq\.com/x/page/(?P<id>[^/]+)\W'
    _PLAYER_PLATFORMS = [11, 2, 1]
    _PLAYER_VERSION = '3.2.19.333'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        formats = []
        for PLAYER_PLATFORM in self._PLAYER_PLATFORMS.copy():
            params = {
                'otype': 'json',
                'platform': PLAYER_PLATFORM,
                'vid': video_id,
                'defnpayver': 1,
                'appver': self._PLAYER_VERSION,
                'defn': 'fhd',
            }
            print(update_url_query('https://vv.video.qq.com/getinfo', query=params))
            webpage = self._download_webpage(update_url_query('https://vv.video.qq.com/getinfo', query=params), video_id)
            data = self._parse_json(self._search_regex(r'QZOutputJson=(.*)\;', webpage, ''), video_id=video_id, transform_source=js_to_json)
            video = data['vl']['vi'][0]
            fn = video['fn']
            title = video['ti']
            td = float(video['td'])
            fvkey = video.get('fvkey')
            # Not to be absolutely accuracy.
            # fp2p = data.get('fp2p')
            iflag = video.get('iflag')
            pl = video.get('pl')
            self.limit = bool(iflag or pl)
            self.vip = video['drm']
            # Priority for range fetch.
            cdn_url_1 = cdn_url_2 = cdn_url_3 = None
            for cdn in video['ul']['ui']:
                cdn_url = cdn['url']
                if 'vip' in cdn_url:
                    continue
                if cdn_url.startswith('http://video.dispatch.tc.qq.com/'):
                    cdn_url_3 = cdn_url
                elif re.search(cdn_url, '(^http://[0-9\.]+/)'):
                    if not cdn_url_2:
                        cdn_url_2 = cdn_url
                elif not cdn_url_1:
                    cdn_url_1 = cdn_url
            if self.limit:
                cdn_url = cdn_url_3 or cdn_url_1 or cdn_url_2
            else:
                cdn_url = cdn_url_1 or cdn_url_2 or cdn_url_3

            dt = cdn['dt']
            if dt == 1:
                type_name = 'flv'
            elif dt == 2:
                type_name = 'mp4'
            else:
                type_name = fn.split('.')[-1]

            _num_clips = video['cl']['fc']

            for fmt in data['fl']['fi']:
                fmt_id = fmt['id']
                fmt_name = fmt['name']
                fmt_cname = fmt['resolution'].lower().split('p')[0]
                print(fmt_cname)
                size = fmt['fs']
                rate = size // td

                fns = fn.split('.')
                fmt_id_num = int(fmt_id)
                fmt_id_prefix = None
                num_clips = 0

                if fmt_id_num > 100000:
                    fmt_id_prefix = 'm'
                elif fmt_id_num > 10000:
                    fmt_id_prefix = 'p'
                    num_clips = _num_clips or 1
                if fmt_id_prefix:
                    fmt_id_name = fmt_id_prefix + str(fmt_id_num % 10000)
                    if fns[1][0] in ('p', 'm') and not fns[1].startswith('mp'):
                        fns[1] = fmt_id_name
                    else:
                        fns.insert(1, fmt_id_name)
                elif fns[1][0] in ('p', 'm') and not fns[1].startswith('mp'):
                    del fns[1]

                urls = []

                if num_clips == 0:
                    filename = '.'.join(fns)
                    url, vip = self.qq_get_final_url(cdn_url, video_id, fmt_id,
                                                filename, fvkey, PLAYER_PLATFORM)
                    if vip:
                        self.vip = vip
                    elif url:
                        # print(url)
                        urls.append(url)
                else:
                    fns.insert(-1, '1')
                    for idx in range(1, num_clips + 1):
                        fns[-2] = str(idx)
                        filename = '.'.join(fns)
                        url, vip = self.qq_get_final_url(cdn_url, video_id, fmt_id,
                                                    filename, fvkey, PLAYER_PLATFORM)
                        if vip:
                            self.vip = vip
                            break
                        elif url:
                            print(url)
                            urls.append(url)
            print(title, rate, fmt_cname)
            exit()
            # exit()

    def qq_get_final_url(self, url, vid, fmt_id, filename, fvkey, platform):
        params = {
            'appver': self._PLAYER_VERSION,
            'otype': 'json',
            'platform': platform,
            'filename': filename,
            'vid': vid,
            'format': fmt_id,
        }

        webpage = self._download_webpage('https://vv.video.qq.com/getkey', video_id=vid, query=params)
        data = self._parse_json(self._search_regex(r'QZOutputJson=(.*)\;', webpage, ''), video_id=vid, transform_source=js_to_json)
        vkey = data.get('key', fvkey)
        if vkey:
            url = '{url}{filename}?vkey={vkey}'.format(**vars())
        else:
            url = None
        vip = data.get('msg') == 'not pay'

        return url, vip
        #     exit()
        #     if 'msg' in data:
        #         assert data['msg'] not in ('vid is wrong', 'vid status wrong'), \
        #             'wrong vid'
        #         PLAYER_PLATFORMS.remove(PLAYER_PLATFORM)
        #         continue
        #
        #     if PLAYER_PLATFORMS and \
        #             profile == 'shd' and \
        #             '"name":"shd"' not in resp.text and \
        #             '"name":"fhd"' not in resp.text:
        #         for infos in self.get_streams_info('hd'):
        #             yield infos
        #         return
        #     break
        #
        # assert 'msg' not in data, data['msg']
        # video = data['vl']['vi'][0]
        # fn = video['fn']
        # title = video['ti']
        # td = float(video['td'])
        # fvkey = video.get('fvkey')
        # # Not to be absolutely accuracy.
        # # fp2p = data.get('fp2p')
        # iflag = video.get('iflag')
        # pl = video.get('pl')
        # self.limit = bool(iflag or pl)
        # self.vip = video['drm']
        #
        # # Priority for range fetch.
        # cdn_url_1 = cdn_url_2 = cdn_url_3 = None
        # for cdn in video['ul']['ui']:
        #     cdn_url = cdn['url']
        #     if 'vip' in cdn_url:
        #         continue
        #     # 'video.dispatch.tc.qq.com' supported keep-alive link.
        #     if cdn_url.startswith('http://video.dispatch.tc.qq.com/'):
        #         cdn_url_3 = cdn_url
        #     # IP host.
        #     elif match1(cdn_url, '(^http://[0-9\.]+/)'):
        #         if not cdn_url_2:
        #             cdn_url_2 = cdn_url
        #     elif not cdn_url_1:
        #         cdn_url_1 = cdn_url
        # if self.limit:
        #     cdn_url = cdn_url_3 or cdn_url_1 or cdn_url_2
        # else:
        #     cdn_url = cdn_url_1 or cdn_url_2 or cdn_url_3
        # # cdn_url = cdn_url_1 or cdn_url_2 or cdn_url_3
        #
        # dt = cdn['dt']
        # if dt == 1:
        #     type_name = 'flv'
        # elif dt == 2:
        #     type_name = 'mp4'
        # else:
        #     type_name = fn.split('.')[-1]
        #
        # _num_clips = video['cl']['fc']
        # for fmt in data['fl']['fi']:
        #     fmt_id = fmt['id']
        #     fmt_name = fmt['name']
        #     fmt_cname = fmt['cname']
        #     size = fmt['fs']
        #     rate = size // td
        #
        #     fns = fn.split('.')
        #     fmt_id_num = int(fmt_id)
        #     fmt_id_prefix = None
        #     num_clips = 0
        #
        #     if fmt_id_num > 100000:
        #         fmt_id_prefix = 'm'
        #     elif fmt_id_num > 10000:
        #         fmt_id_prefix = 'p'
        #         num_clips = _num_clips or 1
        #     if fmt_id_prefix:
        #         fmt_id_name = fmt_id_prefix + str(fmt_id_num % 10000)
        #         if fns[1][0] in ('p', 'm') and not fns[1].startswith('mp'):
        #             fns[1] = fmt_id_name
        #         else:
        #             fns.insert(1, fmt_id_name)
        #     elif fns[1][0] in ('p', 'm') and not fns[1].startswith('mp'):
        #         del fns[1]
        #
        #     urls = []
        #
        #     if num_clips == 0:
        #         filename = '.'.join(fns)
        #         url, vip = qq_get_final_url(cdn_url, self.vid, fmt_id,
        #                                     filename, fvkey, PLAYER_PLATFORM)
        #         if vip:
        #             self.vip = vip
        #         elif url:
        #             urls.append(url)
        #     else:
        #         fns.insert(-1, '1')
        #         for idx in range(1, num_clips + 1):
        #             fns[-2] = str(idx)
        #             filename = '.'.join(fns)
        #             url, vip = qq_get_final_url(cdn_url, self.vid, fmt_id,
        #                                         filename, fvkey, PLAYER_PLATFORM)
        #             if vip:
        #                 self.vip = vip
        #                 break
        #             elif url:
        #                 urls.append(url)
        #
        #     yield title, fmt_name, fmt_cname, type_name, urls, size, rate