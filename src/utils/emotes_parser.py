import logging
import re

from src.config import EMOTES_CDN_PROXY

logger = logging.getLogger(__name__)


class EmotesParser:
    @staticmethod
    def _apply_cdn_proxy(emote_url: str) -> str:
        if EMOTES_CDN_PROXY:
            return f"{EMOTES_CDN_PROXY}{emote_url}"
        return emote_url

    @staticmethod
    def parse_message(text: str) -> str:
        if not text:
            return text

        # Pattern 1: [emote|URL|NAME] or [emote|URL|NAME|zw] - for BTTV, FFZ, 7TV, Twitch/ VKPlay
        emote_pattern_url = r"\[emote\|([^\|]+)\|([^\|\]]+)(?:\|zw)?\]"

        def replace_emote_url(match):
            emote_url = match.group(1)
            emote_name = match.group(2)
            is_zero_wide = match.group(0).endswith("|zw]")
            proxied_url = EmotesParser._apply_cdn_proxy(emote_url)

            if is_zero_wide:
                return (
                    f"[emote_name={emote_name},emote_url={proxied_url},emote_zw=True]"
                )
            return f"[emote_name={emote_name},emote_url={proxied_url}]"

        # Pattern 2: [emote:ID:NAME] - for Kick emotes
        emote_pattern_kick = r"\[emote:(\d+):([^\]]+)\]"

        def replace_emote_kick(match):
            emote_id = match.group(1)
            emote_name = match.group(2)
            emote_url = f"https://files.kick.com/emotes/{emote_id}/fullsize"
            proxied_url = EmotesParser._apply_cdn_proxy(emote_url)
            return f"[emote_name={emote_name},emote_url={proxied_url}]"

        text = re.sub(emote_pattern_url, replace_emote_url, text)
        text = re.sub(emote_pattern_kick, replace_emote_kick, text)
        return text
