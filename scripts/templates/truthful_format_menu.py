from urllib.parse import urlsplit
import re


def audio_format_selector(override):
    if override in (None, '', 'ba', 'bestaudio'):
        return 'ba/b'
    return override


def strict_quality_selector(url, quality, selector):
    if not allow_manual_qualities(url) and re.fullmatch(r'\d+p', quality or '') and selector:
        return selector.split('/', 1)[0]
    return selector


def allow_manual_qualities(url):
    """Do not advertise unverified resolutions for these platform resolvers."""
    try:
        host = (urlsplit(url).hostname or '').lower()
    except (TypeError, ValueError):
        return True
    domains = ('douyin.com', 'iesdouyin.com', 'b23.tv', 'bilibili.com',
               'xhslink.cn', 'xhslink.com', 'xiaohongshu.com', 'weixin.qq.com')
    return not any(host == domain or host.endswith('.' + domain) for domain in domains)
