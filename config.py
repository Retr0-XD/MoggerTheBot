from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
INSTAGRAM_API_KEY = os.getenv('INSTAGRAM_API_KEY')

# Bot configuration
ADMIN_ID = 1436247443  # Bot administrator's Telegram ID

# Load NSFW whitelist from environment (using ALLOWED_USERS for backward compatibility)
NSFW_WHITELIST = os.getenv('ALLOWED_USERS', '').split(',')
NSFW_WHITELIST = [int(id.strip()) for id in NSFW_WHITELIST if id.strip().isdigit()]

# Torrent provider configuration
TORRENT_PROVIDERS = {
    "1337x": {"title": "1337x", "code": "!1337x", "active": True},
    "piratebay": {"title": "The Pirate Bay", "code": "!pb", "active": True},
    "rarbg": {"title": "RARBG", "code": "!rb", "active": False},
    "nyaasi": {"title": "Nyaa.si", "code": "!nyaa", "active": True},
    "yts": {"title": "YTS", "code": "!yts", "active": True},
    "eztv": {"title": "Ez Tv", "code": "!ez", "active": False},
    "ettv": {"title": "Et Tv", "code": "!et", "active": False},
    "torlock": {"title": "Torlock", "code": "!tl", "active": True},
    "tgx": {"title": "Torrent Galaxy", "code": "!tg", "active": True},
    "zooqle": {"title": "Zooqle", "code": "!zoo", "active": False},
    "kickass": {"title": "Kick Ass", "code": "!ka", "active": True},
    "bitsearch": {"title": "Bit Search", "code": "!bs", "active": True},
    "glodls": {"title": "Glodls", "code": "!gl", "active": True},
    "magnetdl": {"title": "magnetDL", "code": "!mdl", "active": True},
    "limetorrent": {"title": "Lime Torrents", "code": "!lt", "active": True},
    "torrentfunk": {"title": "Torrent Funk", "code": "!tf", "active": True},
    "torrentproject": {"title": "Torrent Project", "code": "!tp", "active": True},
    "libgen": {"title": "Libgen", "code": "!lg", "active": True},
    "ybt": {"title": "Your BitTorrent", "code": "!ybt", "active": True}
}

PROVIDERS = {
    'torrenthunt': {
        'name': 'TorrentHunt',
        'base_url': 'https://torrenthunt.p.rapidapi.com/api/search/',
        'headers': {
            'X-RapidAPI-Key': RAPIDAPI_KEY,
            'X-RapidAPI-Host': 'torrenthunt.p.rapidapi.com'
        },
        'sites': [site for site, info in TORRENT_PROVIDERS.items() if info['active']]
    },
    'terabox': {
        'name': 'TeraBox Downloader',
        'base_url': 'https://terabox-downloader-direct-download-link-generator.p.rapidapi.com/fetch',
        'headers': {
            'X-RapidAPI-Key': RAPIDAPI_KEY,
            'X-RapidAPI-Host': 'terabox-downloader-direct-download-link-generator.p.rapidapi.com',
            'Content-Type': 'application/json'
        }
    },
    'instagram': {
        'name': 'Instagram Downloader',
        'base_url': 'https://instagram-scrapper-video-reel-image-downloader-api.p.rapidapi.com/instantdownloader.php',
        'headers': {
            'X-RapidAPI-Key': RAPIDAPI_KEY,
            'X-RapidAPI-Host': 'instagram-scrapper-video-reel-image-downloader-api.p.rapidapi.com',
            'Content-Type': 'application/json'
        }
    }
}
