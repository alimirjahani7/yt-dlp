import html
import re

import requests

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
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
    _TESTS = []

    def find_title(self, url):
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title').get_text()
            return title
        return None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        web_decoded = html.unescape(webpage)
        pattern = re.compile(
            r"https:\/\/(?:\w+\-)?livectorprodmedia\d+-\w+\.licdn\.com\/[a-zA-Z0-9\-]+\/[a-zA-Z0-9\-]+-livemanifest\.ism\/manifest\(format=m3u8-aapl(-v3)?\)")
        matched_urls = [match[0] for match in re.finditer(pattern, web_decoded)]
        media_url = matched_urls[0].replace('aapl)', 'aapl-v3)')
        title = self.find_title(url)
        response = requests.get(media_url)
        result = response.text
        lines = result.replace('\r\n', '\n').split('\n')
        play_list_path = None
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                play_list_path = line
        base_url = media_url.rsplit('/', 1)[0]
        play_list_url = f"{base_url}/{play_list_path}"
        formats = []
        formats.extend(self._extract_m3u8_formats(
            play_list_url, '', 'mp4',
            'm3u8_native', m3u8_id='hls', fatal=False))
        result = {'id': video_id, 'formats': formats}
        if title:
            result['title'] = title
        return result


class LinkedInIE(LinkedInEventIE):
    _VALID_URL = r'https?://(?:www\.)?linkedin\.com/posts/[^/?#]+-(?P<id>\d+)-\w{4}/?(?:[?#]|$)'
