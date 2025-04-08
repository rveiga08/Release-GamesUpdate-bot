import requests
import json
from datetime import datetime
from urllib.parse import quote
from config import Config
from logger import logger
import time

class SteamAPI:
    def __init__(self, api_key=Config.STEAM_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com"
        self.steamdb_url = "https://steamdb.info/api"
        self.cache = {}
        self.cache_expiration = Config.CACHE_EXPIRATION
    
    def _make_request(self, url, params=None, use_cache=True):
        cache_key = f"{url}?{str(params)}"
        
        # Check cache first
        if use_cache and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_expiration:
                return cached_data
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            if use_cache:
                self.cache[cache_key] = (data, time.time())
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Steam API request failed: {e}")
            return None
    
    def get_steam_id_from_url(self, profile_url):
        """Convert Steam profile URL to SteamID64"""
        try:
            # If already a SteamID64 (17 digits)
            if profile_url.isdigit() and len(profile_url) == 17:
                return profile_url
            
            # Extract from URL
            if "steamcommunity.com" not in profile_url:
                return None
                
            if "/id/" in profile_url:
                # Vanity URL
                vanity_name = profile_url.split("/id/")[-1].split("/")[0]
                url = f"{self.base_url}/ISteamUser/ResolveVanityURL/v1/"
                params = {
                    'key': self.api_key,
                    'vanityurl': vanity_name
                }
                data = self._make_request(url, params)
                return data.get('response', {}).get('steamid') if data else None
            else:
                # Direct ID
                steam_id = profile_url.split("/profiles/")[-1].split("/")[0]
                return steam_id if steam_id.isdigit() else None
        except Exception as e:
            logger.error(f"Error extracting Steam ID from URL: {e}")
            return None
    
    def get_owned_games(self, steam_id):
        url = f"{self.base_url}/IPlayerService/GetOwnedGames/v1/"
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'include_appinfo': True,
            'include_played_free_games': True
        }
        data = self._make_request(url, params)
        return data.get('response', {}).get('games', []) if data else None
    
    def get_app_details(self, app_id):
        url = f"https://store.steampowered.com/api/appdetails"
        params = {
            'appids': app_id,
            'l': 'english'
        }
        data = self._make_request(url, params)
        return data.get(str(app_id), {}).get('data') if data else None
    
    def get_steamdb_changelog(self, app_id):
        url = f"{self.steamdb_url}/PatchData/"
        params = {
            'appid': app_id
        }
        data = self._make_request(url, params, use_cache=False)
        
        if not data or not data.get('success'):
            return None
        
        changes = data.get('changes', [])
        if not changes:
            return None
        
        latest_change = changes[0]
        return {
            'build_id': latest_change.get('buildid'),
            'time': latest_change.get('time'),
            'changelog': latest_change.get('change_description'),
            'url': f"https://steamdb.info/app/{app_id}/patchnotes/"
        }
    
    def get_current_build_id(self, app_id):
        """Get the current build ID from SteamDB"""
        changelog = self.get_steamdb_changelog(app_id)
        return changelog.get('build_id') if changelog else None