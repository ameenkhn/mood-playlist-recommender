import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import random
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpotifyClient:
    """Class for interacting with Spotify Web API with enhanced error handling"""
    
    def __init__(self, client_id, client_secret, redirect_uri):
        """
        Initialize Spotify client
        
        Args:
            client_id (str): Spotify client ID
            client_secret (str): Spotify client secret
            redirect_uri (str): Redirect URI for authentication
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp = None
        
    def authenticate(self):
        """Authenticate with Spotify API with enhanced error handling"""
        try:
            if not all([self.client_id, self.client_secret, self.redirect_uri]):
                logger.error("Missing Spotify credentials")
                return False
            
            if (self.client_id == 'your_client_id_here' or 
                self.client_secret == 'your_client_secret_here'):
                logger.error("Please update Spotify credentials in .env file")
                return False
            
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope="user-library-read playlist-read-private playlist-read-collaborative",
                show_dialog=True,
                cache_path=".spotify_cache"
            )
            
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            try:
                user = self.sp.current_user()
                if user and user.get('display_name'):
                    logger.info(f"Successfully authenticated as: {user['display_name']}")
                elif user and user.get('id'):
                    logger.info(f"Successfully authenticated as user: {user['id']}")
                else:
                    logger.info("Successfully authenticated with Spotify")
            except Exception as e:
                logger.warning(f"Authentication successful but couldn't get user info: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Spotify authentication failed: {e}")
            logger.info("Make sure your Spotify credentials are correct and the redirect URI matches your app settings")
            return False
    
    def _is_valid_playlist(self, playlist):
        """
        Validate playlist object to prevent None errors
        
        Args:
            playlist (dict): Playlist object from Spotify API
            
        Returns:
            bool: True if playlist is valid, False otherwise
        """
        if not playlist:
            return False
        
        required_fields = ['name', 'external_urls', 'tracks', 'owner']
        for field in required_fields:
            if not playlist.get(field):
                return False
        
        tracks = playlist.get('tracks', {})
        if not isinstance(tracks, dict) or tracks.get('total', 0) == 0:
            return False
        
        external_urls = playlist.get('external_urls', {})
        if not isinstance(external_urls, dict) or not external_urls.get('spotify'):
            return False
        
        owner = playlist.get('owner', {})
        if not isinstance(owner, dict):
            return False
        
        return True
    
    def _extract_playlist_info(self, playlist):
        """
        Safely extract playlist information with comprehensive error handling
        
        Args:
            playlist (dict): Playlist object from Spotify API
            
        Returns:
            dict: Extracted playlist information or None if extraction fails
        """
        try:
            name = playlist.get('name', 'Unknown Playlist')
            url = playlist.get('external_urls', {}).get('spotify', '')
            description = playlist.get('description') or 'No description available'
            
            tracks = playlist.get('tracks', {})
            tracks_count = tracks.get('total', 0) if isinstance(tracks, dict) else 0
            
            owner = playlist.get('owner', {})
            owner_name = 'Unknown User'
            if isinstance(owner, dict):
                owner_name = owner.get('display_name') or owner.get('id', 'Unknown User')
            
            images = playlist.get('images', [])
            image_url = ''
            if isinstance(images, list) and images:
                first_image = images[0]
                if isinstance(first_image, dict):
                    image_url = first_image.get('url', '')
            
            playlist_info = {
                'name': name,
                'url': url,
                'description': description[:200] + '...' if len(description) > 200 else description,
                'tracks_count': tracks_count,
                'owner': owner_name,
                'image': image_url
            }
            
            return playlist_info
            
        except Exception as e:
            logger.error(f"Error extracting playlist info: {e}")
            return None
    
    def _remove_duplicates(self, playlists):
        """
        Remove duplicate playlists based on URL
        
        Args:
            playlists (list): List of playlist dictionaries
            
        Returns:
            list: List of unique playlists
        """
        unique_playlists = []
        seen_urls = set()
        
        for playlist in playlists:
            if not playlist or not isinstance(playlist, dict):
                continue
                
            url = playlist.get('url', '')
            if url and url not in seen_urls:
                unique_playlists.append(playlist)
                seen_urls.add(url)
        
        return unique_playlists
    
    def search_mood_playlists(self, mood_keywords, limit=10):
        """
        Search for playlists based on mood keywords with robust error handling
        
        Args:
            mood_keywords (list): List of keywords related to the mood
            limit (int): Maximum number of playlists to search per keyword
            
        Returns:
            list: List of playlist dictionaries
        """
        if not self.sp:
            logger.error("Spotify client not authenticated")
            return []
        
        if not mood_keywords or not isinstance(mood_keywords, list):
            logger.error("Invalid mood keywords provided")
            return []
        
        try:
            all_playlists = []
            
            for keyword in mood_keywords:
                if not keyword or not isinstance(keyword, str):
                    continue
                    
                logger.info(f"Searching playlists for keyword: {keyword}")
                
                try:
                    results = self.sp.search(
                        q=f'"{keyword}"',  # Use quotes for better matching
                        type='playlist',
                        limit=min(limit, 50),  # Spotify max is 50
                        market='US'  # Add market for better results
                    )
                    
                    if not results or not isinstance(results, dict):
                        logger.warning(f"No results returned for keyword: {keyword}")
                        continue
                    
                    playlists_data = results.get('playlists', {})
                    if not isinstance(playlists_data, dict):
                        logger.warning(f"Invalid playlists data for keyword: {keyword}")
                        continue
                    
                    playlists = playlists_data.get('items', [])
                    if not isinstance(playlists, list):
                        logger.warning(f"Invalid playlists items for keyword: {keyword}")
                        continue
                    
                    if not playlists:
                        logger.info(f"No playlists found for keyword: {keyword}")
                        continue
                    
                    logger.info(f"Found {len(playlists)} playlists for keyword: {keyword}")
                    
                    for playlist in playlists:
                        # Comprehensive validation
                        if not self._is_valid_playlist(playlist):
                            continue
                        
                        playlist_info = self._extract_playlist_info(playlist)
                        if playlist_info and playlist_info.get('url'):
                            all_playlists.append(playlist_info)
                    
                    time.sleep(0.1)
                        
                except Exception as e:
                    logger.warning(f"Error searching for keyword '{keyword}': {e}")
                    continue
            
            unique_playlists = self._remove_duplicates(all_playlists)
            logger.info(f"Found {len(unique_playlists)} unique playlists total")
            
            return unique_playlists
            
        except Exception as e:
            logger.error(f"Error in search_mood_playlists: {e}")
            return []
    
    def get_mood_playlist_recommendation(self, mood_keywords):
        """
        Get a single playlist recommendation for the detected mood
        
        Args:
            mood_keywords (list): List of keywords related to the mood
            
        Returns:
            dict: Recommended playlist information or None
        """
        if not mood_keywords:
            logger.warning("No mood keywords provided")
            return None
        
        try:
            playlists = self.search_mood_playlists(mood_keywords, limit=20)
            
            if not playlists:
                logger.warning("No playlists found for the given mood keywords")
                # Try with a broader search
                logger.info("Attempting broader search...")
                broader_keywords = ['music', 'playlist', 'songs']
                playlists = self.search_mood_playlists(broader_keywords, limit=10)
            
            if not playlists:
                logger.error("No playlists found even with broader search")
                return None
            
            quality_playlists = [p for p in playlists if p.get('tracks_count', 0) >= 10]
            
            if not quality_playlists:
                quality_playlists = playlists  # Fall back to any playlist
            
            recommended_playlist = random.choice(quality_playlists)
            logger.info(f"Recommended playlist: {recommended_playlist.get('name', 'Unknown')}")
            
            return recommended_playlist
            
        except Exception as e:
            logger.error(f"Error getting playlist recommendation: {e}")
            return None
    
    def open_playlist_in_browser(self, playlist_url):
        """
        Open playlist URL in default browser with error handling
        
        Args:
            playlist_url (str): Spotify playlist URL
        """
        if not playlist_url or not isinstance(playlist_url, str):
            logger.error("Invalid playlist URL provided")
            return False
        
        try:
            if not playlist_url.startswith('https://open.spotify.com/'):
                logger.error(f"Invalid Spotify URL format: {playlist_url}")
                return False
            
            webbrowser.open(playlist_url)
            logger.info(f"Opened playlist in browser: {playlist_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open playlist in browser: {e}")
            return False
    
    def get_featured_playlists(self, limit=20):
        """
        Get featured playlists as fallback option
        
        Args:
            limit (int): Number of playlists to retrieve
            
        Returns:
            list: List of featured playlist dictionaries
        """
        if not self.sp:
            logger.error("Spotify client not authenticated")
            return []
        
        try:
            results = self.sp.featured_playlists(limit=limit)
            
            if not results or not isinstance(results, dict):
                return []
            
            playlists_data = results.get('playlists', {})
            if not isinstance(playlists_data, dict):
                return []
            
            playlists = playlists_data.get('items', [])
            if not isinstance(playlists, list):
                return []
            
            featured_playlists = []
            for playlist in playlists:
                if self._is_valid_playlist(playlist):
                    playlist_info = self._extract_playlist_info(playlist)
                    if playlist_info:
                        featured_playlists.append(playlist_info)
            
            return featured_playlists
            
        except Exception as e:
            logger.error(f"Error getting featured playlists: {e}")
            return []
    
    def test_connection(self):
        """
        Test Spotify API connection
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        if not self.sp:
            return False
        
        try:
            self.sp.current_user()
            return True
        except Exception as e:
            logger.error(f"Spotify connection test failed: {e}")
            return False