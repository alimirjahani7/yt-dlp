import itertools
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    float_or_none,
    int_or_none,
    mimetype2ext,
    srt_subtitles_timecode,
    traverse_obj,
    try_get,
    url_or_none,
    urlencode_postdata,
    urljoin,
)


class LinkedInBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'linkedin'
    _logged_in = False
    _LOGIN_URL = 'https://www.linkedin.com/uas/login?trk=learning'

    def _perform_login(self, username, password):
        if self._logged_in:
            return

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')
        action_url = urljoin(self._LOGIN_URL, self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>.+?)\1', login_page, 'post url',
            default='https://www.linkedin.com/uas/login-submit', group='url'))
        data = self._hidden_inputs(login_page)
        data.update({
            'session_key': username,
            'session_password': password,
        })
        login_submit_page = self._download_webpage(
            action_url, None, 'Logging in',
            data=urlencode_postdata(data))
        error = self._search_regex(
            r'<span[^>]+class="error"[^>]*>\s*(.+?)\s*</span>',
            login_submit_page, 'error', default=None)
        if error:
            raise ExtractorError(error, expected=True)
        LinkedInBaseIE._logged_in = True


class LinkedInEventIE(LinkedInBaseIE):
    _VALID_URL = r'https:\/\/www\.linkedin\.com\/events\/(?P<id>\d+)\/comments\/'
    _TESTS = [{
        'url': 'https://www.linkedin.com/posts/mishalkhawaja_sendinblueviews-toronto-digitalmarketing-ugcPost-6850898786781339649-mM20',
        'info_dict': {
            'id': '6850898786781339649',
            'ext': 'mp4',
            'title': 'Mishal K. on LinkedIn: #sendinblueviews #toronto #digitalmarketing #nowhiring #sendinblue…',
            'description': 'md5:2998a31f6f479376dd62831f53a80f71',
            'uploader': 'Mishal K.',
            'thumbnail': 're:^https?://media.licdn.com/dms/image/.*$',
            'like_count': int
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        with open('rrr.txt', 'w') as f:
            f.write(webpage)

        # video_attrs = extract_attributes(self._search_regex(
        #     r'https:\/\/livectorprodmedia\d+-\w+\.licdn\.com\/[a-zA-Z0-9\-]+\/L4[a-zA-Z0-9\-]+-livemanifest\.ism\/manifest\(format=m3u8-aapl(-v3)?\)',
        #     webpage, 'video'))
        return {
            'id': video_id,
            'formats': [{
                'url': 'https://livectorprodmedia17-euwe.licdn.com/bceb38d6-6983-487a-9da2-7e172388065c/L4E63f3cb0ea5c68000-livemanifest.ism/manifest(format=m3u8-aapl-v3)',
                'ext': 'm3u8',
                'tbr': 0
            }],
        }


class LinkedInIE(LinkedInEventIE):
    _VALID_URL = r'https?://(?:www\.)?linkedin\.com/posts/[^/?#]+-(?P<id>\d+)-\w{4}/?(?:[?#]|$)'
