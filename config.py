import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for application settings"""
    
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'your_client_id_here')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'your_client_secret_here')
    SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8080/callback')
    
    MOOD_MAPPING = {
        'happy': ['happy', 'party', 'upbeat', 'energetic', 'dance'],
        'sad': ['sad', 'melancholy', 'blues', 'emotional', 'heartbreak'],
        'angry': ['rock', 'metal', 'aggressive', 'intense', 'hardcore'],
        'fear': ['ambient', 'calm', 'peaceful', 'meditation', 'relaxing'],
        'surprise': ['pop', 'hits', 'trending', 'viral', 'popular'],
        'disgust': ['alternative', 'indie', 'experimental', 'underground'],
        'neutral': ['chill', 'lofi', 'background', 'study', 'focus']
    }
    
    CAMERA_INDEX = 0
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    
    DETECTION_CONFIDENCE = 0.7
    FRAME_SKIP = 30  