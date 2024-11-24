import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from config import PROVIDERS, TORRENT_PROVIDERS
from pornhub_api.api import PornhubApi
from hqporner_api import Client, Quality
import logging

class BaseProvider:
    def __init__(self, provider_key: str):
        self.config = PROVIDERS.get(provider_key)
        if not self.config:
            raise ValueError(f"Invalid provider key: {provider_key}")
        
    async def _make_request(self, endpoint: str = '', method: str = 'GET', data: Dict = None, params: Dict = None) -> Dict:
        async with aiohttp.ClientSession() as session:
            url = f"{self.config['base_url']}{f'/{endpoint}' if endpoint else ''}"
            kwargs = {
                'headers': self.config['headers'],
                'params': params,
                'json': data if method == 'POST' and data else None
            }
            
            if method == 'GET':
                async with session.get(url, **kwargs) as response:
                    return await response.json()
            else:
                async with session.post(url, **kwargs) as response:
                    return await response.json()

class TorrentProvider(BaseProvider):
    def __init__(self):
        super().__init__('torrenthunt')
        self.current_site = 'yts'  # default site
        self.providers_info = TORRENT_PROVIDERS
        
    def get_current_site_info(self) -> Dict[str, str]:
        """Get current torrent site info"""
        for site_id, info in self.providers_info.items():
            if site_id == self.current_site:
                return info
        return self.providers_info['yts']  # fallback to YTS
        
    def get_available_sites(self) -> List[Dict[str, Any]]:
        """Get list of available torrent sites"""
        return [
            {'id': site_id, **info}
            for site_id, info in self.providers_info.items()
            if info['active']
        ]
        
    def set_site(self, site: str) -> bool:
        """Set the current torrent site"""
        if site in self.providers_info and self.providers_info[site]['active']:
            self.current_site = site
            return True
        return False
        
    async def search(self, query: str, limit: int = 10, site: Optional[str] = None) -> List[Dict]:
        """Search for torrents with specified provider"""
        if site and site in [s['id'] for s in self.get_available_sites()]:
            self.current_site = site
            
        params = {
            'site': self.current_site,
            'query': query,
            'limit': str(limit)
        }
        
        try:
            logging.info(f"Searching torrents with params: {params}")
            response = await self._make_request('', params=params)
            logging.info(f"Got response: {response}")
            
            if not response:
                logging.error("Empty response from API")
                return []
                
            # Handle error response
            if isinstance(response, dict) and response.get('message'):
                logging.error(f"API error: {response['message']}")
                return []
                
            # Handle successful response
            if isinstance(response, dict) and response.get('status') == 200 and 'items' in response:
                results = []
                for item in response['items']:
                    try:
                        # Handle YTS-style responses with multiple torrents per item
                        if 'torrents' in item:
                            for torrent in item['torrents']:
                                result = {
                                    'title': f"{item['name']} ({torrent['quality']}) {torrent['type']}",
                                    'size': torrent['size'],
                                    'type': torrent['type'],
                                    'quality': torrent['quality'],
                                    'magnet': torrent['magnet'],
                                    'url': item.get('link', ''),
                                    'rating': item.get('rating', 'N/A'),
                                    'genre': ', '.join(item.get('genre', [])),
                                    'description': item.get('description', ''),
                                    'provider': self.current_site
                                }
                                results.append(result)
                        else:
                            # Handle standard torrent response
                            result = {
                                'title': item.get('name', 'Unknown'),
                                'size': item.get('size', 'N/A'),
                                'magnet': item.get('magnet', ''),
                                'url': item.get('link', ''),
                                'provider': self.current_site
                            }
                            results.append(result)
                    except Exception as e:
                        logging.error(f"Error processing torrent item: {str(e)}")
                        continue
                        
                return results[:limit]
                
            logging.error(f"Unexpected response format: {response}")
            return []
            
        except Exception as e:
            logging.error(f"Error searching torrents: {str(e)}")
            return []
    
    async def get_config(self) -> Dict:
        """Get available torrent sites and configuration"""
        try:
            result = await self._make_request('config')
            return result
        except Exception as e:
            logging.error(f"Error getting torrent config: {str(e)}")
            return {}
    
    def get_current_site_info(self) -> Dict[str, str]:
        """Get information about current torrent site"""
        info = self.providers_info.get(self.current_site, {})
        return {
            'id': self.current_site,
            'title': info.get('title', self.current_site),
            'code': info.get('code', '')
        }

class MediaDownloader(BaseProvider):
    def __init__(self):
        super().__init__('all_media')
    
    async def download_info(self, url: str) -> Dict:
        params = {'url': url}
        return await self._make_request('download', params)

class AllMediaProvider(BaseProvider):
    def __init__(self):
        super().__init__('all_media')
        self.boundary = "---011000010111000001101001"
        
    async def download(self, url: str, endpoint: str = 'all') -> Dict:
        """Download media from various platforms"""
        try:
            headers = self.config['headers'].copy()
            headers['Content-Type'] = f'multipart/form-data; boundary={self.boundary}'
            
            # Construct form-data payload
            payload = (
                f"-----{self.boundary}\r\n"
                f"Content-Disposition: form-data; name=\"url\"\r\n\r\n"
                f"{url}\r\n"
                f"-----{self.boundary}--\r\n\r\n"
            )
            
            endpoint_url = (
                self.config['base_url'] if endpoint == 'all'
                else f"{self.config['base_url'].replace('/all', '')}/{endpoint}"
            )
            
            logging.info(f"Downloading from {endpoint_url} with URL: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint_url, data=payload, headers=headers) as response:
                    result = await response.json()
                    logging.info(f"Got response: {result}")
                    return result
                    
        except Exception as e:
            logging.error(f"Error downloading media: {str(e)}")
            return {"error": str(e)}
            
    async def spotify_search(self, query: str) -> Dict:
        """Search for tracks on Spotify"""
        try:
            headers = self.config['headers'].copy()
            headers['Content-Type'] = f'multipart/form-data; boundary={self.boundary}'
            
            payload = (
                f"-----{self.boundary}\r\n"
                f"Content-Disposition: form-data; name=\"q\"\r\n\r\n"
                f"{query}\r\n"
                f"-----{self.boundary}--\r\n\r\n"
            )
            
            endpoint_url = f"{self.config['base_url'].replace('/all', '')}/spotify-search"
            
            logging.info(f"Searching Spotify for: {query}")
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint_url, data=payload, headers=headers) as response:
                    result = await response.json()
                    logging.info(f"Got Spotify search results: {result}")
                    return result
                    
        except Exception as e:
            logging.error(f"Error searching Spotify: {str(e)}")
            return {"error": str(e)}

class InstagramScraper(BaseProvider):
    def __init__(self):
        super().__init__('instagram')
    
    async def get_media_info(self, url: str) -> Dict:
        params = {'url': url}
        return await self._make_request('media-info', params)

class TeraBoxProvider(BaseProvider):
    def __init__(self):
        super().__init__('terabox')
    
    async def get_download_link(self, url: str) -> Dict:
        """Get direct download link for TeraBox URL"""
        try:
            result = await self._make_request(method='POST', data={'url': url})
            if not result:
                return {'error': 'No response from TeraBox API'}
                
            if result.get('status') == 'error' or result.get('error'):
                return {'error': result.get('message') or result.get('error')}
                
            # Extract download URL from response
            download_url = result.get('url') or result.get('download_url')
            if not download_url:
                return {'error': 'No download URL found in response'}
                
            return {'download_url': download_url}
            
        except Exception as e:
            logging.error(f"Error getting TeraBox download link: {str(e)}")
            return {'error': str(e)}

class InstagramProvider(BaseProvider):
    def __init__(self):
        super().__init__('instagram')
    
    async def get_media(self, url: str, content_type: str = 'reel') -> Dict:
        """Get media download link from Instagram URL
        
        Args:
            url: Instagram URL
            content_type: Type of content ('reel', 'post', 'igtv')
        """
        try:
            result = await self._make_request(method='POST', data={
                'url': url,
                'type': content_type
            })
            
            if not result:
                return {'error': 'No response from Instagram API'}
                
            if result.get('status') == 'error' or result.get('error'):
                return {'error': result.get('message') or result.get('error')}
                
            # Handle different response formats
            if result.get('download_url'):
                return {'download_url': result['download_url']}
            elif result.get('urls'):
                return {'urls': result['urls']}
            elif result.get('medias'):
                return {'urls': [media['url'] for media in result['medias'] if media.get('url')]}
            else:
                return {'error': 'No download URL found in response'}
                
        except Exception as e:
            logging.error(f"Error getting Instagram media: {str(e)}")
            return {'error': str(e)}

class NSFWProvider:
    def __init__(self):
        self.ph = PornhubApi()
        self.hq = Client()
        
    async def search_pornhub(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for videos on PornHub"""
        try:
            results = []
            data = self.ph.search.search(query, ordering="mostviewed", period="weekly")
            
            for video in data.videos[:limit]:
                results.append({
                    'title': video.title,
                    'url': video.url,
                    'duration': video.duration,
                    'views': video.views,
                    'rating': video.rating,
                    'thumbnail': video.default_thumb
                })
            return results
        except Exception as e:
            logging.error(f"Error searching PornHub: {str(e)}")
            return []
            
    async def search_hqporner(self, query: str) -> List[Dict]:
        """Search for videos on HQPorner"""
        try:
            results = self.hq.search(query)
            videos = []
            
            for video in results:
                try:
                    video_info = {
                        'title': video.title,
                        'url': video.url,
                        'duration': getattr(video, 'duration', 'N/A'),
                        'quality': getattr(video, 'quality', Quality.HD),
                        'thumbnail': getattr(video, 'thumbnail', '')
                    }
                    videos.append(video_info)
                except Exception as ve:
                    logging.error(f"Error processing HQPorner video: {str(ve)}")
                    continue
                    
            return videos
        except Exception as e:
            logging.error(f"Error searching HQPorner: {str(e)}")
            return []
            
    async def get_pornhub_stars(self) -> List[Dict]:
        """Get list of popular PornHub stars"""
        try:
            # Using search_stars instead of direct stars access
            stars = self.ph.search.search_stars()[:20]  # Limit to top 20
            return [{
                'name': star.name,
                'url': star.url,
                'videos': getattr(star, 'video_count', 'N/A'),
                'rank': getattr(star, 'rank', 'N/A')
            } for star in stars]
        except Exception as e:
            logging.error(f"Error getting PornHub stars: {str(e)}")
            return []
            
    async def get_hqporner_actress_videos(self, actress: str) -> List[Dict]:
        """Get videos by actress on HQPorner"""
        try:
            results = self.hq.actress(actress)
            videos = []
            
            for video in results:
                try:
                    video_info = {
                        'title': video.title,
                        'url': video.url,
                        'duration': getattr(video, 'duration', 'N/A'),
                        'quality': getattr(video, 'quality', Quality.HD),
                        'thumbnail': getattr(video, 'thumbnail', '')
                    }
                    videos.append(video_info)
                except Exception as ve:
                    logging.error(f"Error processing HQPorner video: {str(ve)}")
                    continue
                    
            return videos
        except Exception as e:
            logging.error(f"Error getting HQPorner actress videos: {str(e)}")
            return []
            
    async def search_xvideos(self, query: str) -> List[Dict]:
        """Search for videos on XVideos using RapidAPI"""
        try:
            # Using TeraBox provider's config for now since we removed all_media
            config = PROVIDERS.get('terabox')
            headers = config['headers'].copy()
            
            async with aiohttp.ClientSession() as session:
                url = "https://xvideos-api.p.rapidapi.com/search"
                params = {"query": query}
                
                async with session.get(url, headers=headers, params=params) as response:
                    result = await response.json()
                    
                    if not result or 'results' not in result:
                        return []
                        
                    videos = []
                    for video in result['results'][:10]:  # Limit to 10 results
                        videos.append({
                            'title': video.get('title', 'No Title'),
                            'url': video.get('url', ''),
                            'duration': video.get('duration', 'N/A'),
                            'quality': video.get('quality', 'N/A'),
                            'views': video.get('views', 'N/A'),
                            'rating': video.get('rating', 'N/A')
                        })
                    return videos
                    
        except Exception as e:
            logging.error(f"Error searching XVideos: {str(e)}")
            return []
