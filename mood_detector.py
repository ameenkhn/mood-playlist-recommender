import cv2
import numpy as np
import random
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MoodDetector:
    """Class for detecting mood from facial expressions using basic OpenCV"""
    
    def __init__(self, camera_index=0, frame_width=640, frame_height=480):
        """
        Initialize mood detector
        
        Args:
            camera_index (int): Camera index for OpenCV
            frame_width (int): Camera frame width
            frame_height (int): Camera frame height
        """
        self.camera_index = camera_index
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.cap = None
        self.frame_count = 0
        
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            logger.info("OpenCV cascades loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load OpenCV cascades: {e}")
            self.face_cascade = None
            self.smile_cascade = None
            self.eye_cascade = None
        
        self.emotions = ['happy', 'sad', 'neutral', 'angry', 'surprise']
        self.current_emotion_index = 0
        self.last_emotion_time = time.time()
        self.emotion_duration = 10  
        
    def initialize_camera(self):
        """Initialize camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            
            if not self.cap.isOpened():
                raise Exception("Could not open camera")
                
            logger.info("Camera initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def detect_faces_and_features(self, frame):
        """
        Detect faces and basic features using OpenCV
        
        Args:
            frame: OpenCV frame/image
            
        Returns:
            dict: Dictionary with face detection results
        """
        if self.face_cascade is None:
            return {'faces': 0, 'smiles': 0, 'eyes': 0}
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            smiles = 0
            eyes = 0
            
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                if self.smile_cascade is not None:
                    smile_rects = self.smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
                    smiles += len(smile_rects)
                    
                    for (sx, sy, sw, sh) in smile_rects:
                        cv2.rectangle(roi_color, (sx, sy), (sx+sw, sy+sh), (0, 255, 0), 2)
                
                if self.eye_cascade is not None:
                    eye_rects = self.eye_cascade.detectMultiScale(roi_gray)
                    eyes += len(eye_rects)
                    
                    for (ex, ey, ew, eh) in eye_rects:
                        cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 255), 2)
            
            return {'faces': len(faces), 'smiles': smiles, 'eyes': eyes}
            
        except Exception as e:
            logger.warning(f"Error detecting faces and features: {e}")
            return {'faces': 0, 'smiles': 0, 'eyes': 0}
    
    def simple_emotion_logic(self, features):
        """
        Simple emotion detection based on detected features
        
        Args:
            features (dict): Dictionary with face detection results
            
        Returns:
            str: Detected emotion or None
        """
        if features['faces'] == 0:
            return None
        
        if features['smiles'] > 0:
            return 'happy'
        elif features['eyes'] >= 2:
            return 'neutral'
        else:
            return 'sad'
    
    def demo_emotion_rotation(self):
        """
        Demo mode that rotates through emotions for testing
        This simulates emotion detection for demo purposes
        
        Returns:
            str: Current demo emotion
        """
        current_time = time.time()
        
        if current_time - self.last_emotion_time > self.emotion_duration:
            self.current_emotion_index = (self.current_emotion_index + 1) % len(self.emotions)
            self.last_emotion_time = current_time
            logger.info(f"Demo mode: Switching to emotion '{self.emotions[self.current_emotion_index]}'")
        
        return self.emotions[self.current_emotion_index]
    
    def detect_mood_from_frame(self, frame):
        """
        Detect mood from a single frame
        
        Args:
            frame: OpenCV frame/image
            
        Returns:
            str: Detected emotion or None if no face detected
        """
        try:
            features = self.detect_faces_and_features(frame)
            
            if features['faces'] > 0:
                emotion = self.simple_emotion_logic(features)
                
                if emotion:
                    logger.info(f"OpenCV detected emotion: {emotion}")
                    return emotion
            
            demo_emotion = self.demo_emotion_rotation()
            logger.info(f"Demo mode emotion: {demo_emotion}")
            return demo_emotion
            
        except Exception as e:
            logger.warning(f"Could not detect emotion from frame: {e}")
            return None
    
    def capture_and_detect(self, frame_skip=30):
        """
        Capture frame from camera and detect mood
        
        Args:
            frame_skip (int): Process every nth frame for performance
            
        Returns:
            tuple: (detected_mood, frame) or (None, None) if failed
        """
        if not self.cap or not self.cap.isOpened():
            logger.error("Camera not initialized")
            return None, None
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to read frame from camera")
                return None, None
            
            frame = cv2.flip(frame, 1)
            
            self.frame_count += 1
            if self.frame_count % frame_skip != 0:
                return None, frame
            
            mood = self.detect_mood_from_frame(frame)
            
            return mood, frame
            
        except Exception as e:
            logger.error(f"Error during capture and detection: {e}")
            return None, None
    
    def release(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()
            logger.info("Camera resources released")