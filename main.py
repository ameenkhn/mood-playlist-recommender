import cv2
import time
import sys
import logging
from typing import Optional, Tuple
from config import Config
from mood_detector import MoodDetector
from spotify_client import SpotifyClient

try:
    from cv2 import rectangle, addWeighted, putText, FONT_HERSHEY_SIMPLEX, imshow, waitKey
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MoodPlaylistRecommender:
    """Main application class"""
    
    def __init__(self):
        """Initialize the mood playlist recommender"""
        self.config = Config()
        self.mood_detector = MoodDetector(
            camera_index=self.config.CAMERA_INDEX,
            frame_width=self.config.FRAME_WIDTH,
            frame_height=self.config.FRAME_HEIGHT
        )
        self.spotify_client = SpotifyClient(
            client_id=self.config.SPOTIFY_CLIENT_ID,
            client_secret=self.config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=self.config.SPOTIFY_REDIRECT_URI
        )
        self.last_recommendation_time = 0
        self.recommendation_cooldown = 10  # seconds
        
    def initialize(self) -> bool:
        """Initialize all components"""
        logger.info("Initializing Mood-Based Playlist Recommender...")
        
        if (self.config.SPOTIFY_CLIENT_ID == 'your_client_id_here' or 
            self.config.SPOTIFY_CLIENT_SECRET == 'your_client_secret_here'):
            logger.error("Please set up your Spotify credentials in .env file")
            logger.info("1. Go to https://developer.spotify.com/dashboard")
            logger.info("2. Create a new app")
            logger.info("3. Copy Client ID and Client Secret to .env file")
            return False
        
        # Initialize camera
        if not self.mood_detector.initialize_camera():
            return False
        
        # Authenticate with Spotify
        if not self.spotify_client.authenticate():
            return False
        
        logger.info("Initialization complete!")
        return True
    
    def get_mood_keywords(self, detected_mood: str) -> list:
        """
        Get playlist keywords based on detected mood
        
        Args:
            detected_mood (str): Detected emotion/mood
            
        Returns:
            list: List of keywords for playlist search
        """
        return self.config.MOOD_MAPPING.get(detected_mood, self.config.MOOD_MAPPING['neutral'])
    
    def recommend_playlist(self, mood: str) -> bool:
        """
        Recommend playlist based on detected mood
        
        Args:
            mood (str): Detected mood/emotion
            
        Returns:
            bool: True if playlist was successfully recommended
        """
        logger.info(f"🎭 Detected mood: {mood.upper()}")
        
        # Get mood-based keywords
        keywords = self.get_mood_keywords(mood)
        logger.info(f"🔍 Searching for playlists with keywords: {', '.join(keywords)}")
        
        # Get playlist recommendation
        playlist = self.spotify_client.get_mood_playlist_recommendation(keywords)
        
        if playlist:
            print("\n" + "="*60)
            print(f"🎵 PLAYLIST RECOMMENDATION FOR '{mood.upper()}' MOOD:")
            print(f"📝 Name: {playlist['name']}")
            print(f"👤 Creator: {playlist['owner']}")
            print(f"🎶 Tracks: {playlist['tracks_count']}")
            print(f"📋 Description: {playlist['description'][:100]}...")
            print(f"🔗 URL: {playlist['url']}")
            print("="*60)
            
            # Open playlist in browser
            self.spotify_client.open_playlist_in_browser(playlist['url'])
            
            self.last_recommendation_time = time.time()
            return True
        else:
            logger.warning(f"No playlist found for mood: {mood}")
            return False
    
    def draw_overlay(self, frame, detected_mood: Optional[str] = None, detection_count: int = 0, required_stability: int = 3) -> None:
        """
        Draw overlay information on the frame
        
        Args:
            frame: OpenCV frame
            detected_mood (str): Current detected mood
            detection_count (int): Current detection count
            required_stability (int): Required stable detections
        """
        # Add semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Add text
        cv2.putText(frame, "Mood Playlist Recommender", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        if detected_mood:
            cv2.putText(frame, f"Mood: {detected_mood.upper()}", (20, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Stability: {detection_count}/{required_stability}", (20, 85), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        else:
            cv2.putText(frame, "Analyzing...", (20, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def ask_try_again(self) -> bool:
        """
        Ask user if they want to try again
        
        Returns:
            bool: True if user wants to try again, False otherwise
        """
        while True:
            print("\n" + "="*50)
            response = input("🔄 Would you like to try again? (y/n): ").strip().lower()
            
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                print("👋 Thank you for using Mood-Based Playlist Recommender!")
                return False
            else:
                print("❌ Please enter 'y' for yes or 'n' for no.")
    
    def detect_mood_single_cycle(self) -> Optional[str]:
        """
        Run a single mood detection cycle
        
        Returns:
            str: Detected mood or None if detection failed
        """
        logger.info("🚀 Starting mood detection...")
        logger.info("📷 Look at the camera and show your emotion!")
        logger.info("⌨️  Press 'q' to quit early")
        
        last_mood: Optional[str] = None
        mood_stability_count = 0
        required_stability = 3  # Require same mood for 3 consecutive detections
        
        try:
            while mood_stability_count < required_stability:
                # Capture and detect mood
                detected_mood, frame = self.mood_detector.capture_and_detect(
                    frame_skip=self.config.FRAME_SKIP
                )
                
                if frame is not None:
                    # Draw overlay on frame
                    self.draw_overlay(frame, detected_mood, mood_stability_count, required_stability)
                    
                    # Display frame
                    cv2.imshow('Mood-Based Playlist Recommender', frame)
                
                # Handle mood stability
                if detected_mood:
                    if detected_mood == last_mood:
                        mood_stability_count += 1
                        logger.info(f"Mood stability: {mood_stability_count}/{required_stability} - {detected_mood}")
                    else:
                        last_mood = detected_mood
                        mood_stability_count = 1
                        logger.info(f"New mood detected: {detected_mood}")
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("Detection cancelled by user")
                    cv2.destroyAllWindows()
                    return None
            
            # Close camera window after successful detection
            cv2.destroyAllWindows()
            logger.info(f"✅ Mood detection complete: {last_mood}")
            return last_mood
            
        except Exception as e:
            logger.error(f"Error during mood detection: {e}")
            cv2.destroyAllWindows()
            return None
    
    def run(self) -> None:
        """Run the main application loop"""
        if not self.initialize():
            logger.error("Initialization failed. Exiting...")
            return
        
        try:
            while True:
                # Run single mood detection cycle
                detected_mood = self.detect_mood_single_cycle()
                
                if detected_mood:
                    # Recommend playlist based on detected mood
                    success = self.recommend_playlist(detected_mood)
                    
                    if not success:
                        print("❌ Failed to get playlist recommendation.")
                else:
                    print("❌ Mood detection was cancelled or failed.")
                
                # Ask if user wants to try again
                if not self.ask_try_again():
                    break
                
                # Small delay before next cycle
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        finally:
            # Cleanup
            self.mood_detector.release()
            cv2.destroyAllWindows()
            logger.info("Application terminated successfully")

def main() -> None:
    """Main function"""
    print("\n🎵 Mood-Based Spotify Playlist Recommender 🎵")
    print("=" * 50)
    print("📋 How it works:")
    print("1. Camera will analyze your facial expression")
    print("2. Once a stable mood is detected, camera stops")
    print("3. You'll get a playlist recommendation")
    print("4. You can choose to try again or exit")
    print("=" * 50)
    
    try:
        app = MoodPlaylistRecommender()
        app.run()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()