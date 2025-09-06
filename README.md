# 🎵 Mood-Based Spotify Playlist Recommender

An intelligent Python application that analyzes your facial expressions in real-time to detect your mood and automatically recommends matching Spotify playlists.  
Using computer vision and machine learning, it creates a **personalized music experience** based on your emotions — all while keeping your data private.

---

## ✨ Features

✅ **Real-time Mood Detection** – Uses your webcam to analyze facial expressions  
✅ **Emotion Recognition** – Powered by [DeepFace](https://github.com/serengil/deepface) for accurate emotion detection  
✅ **Smart Playlist Matching** – Maps emotions to relevant music genres and moods  
✅ **Spotify Integration** – Seamlessly searches and opens playlists in your browser  
✅ **Cross-platform** – Works on Windows, macOS, and Linux  
✅ **Privacy-focused** – All processing happens locally on your device  

---

## 🎯 How It Works

1. **Face Detection** – Captures video from your webcam  
2. **Emotion Analysis** – Uses DeepFace to analyze your dominant facial expression  
3. **Mood Mapping** – Converts emotions into music moods:
   - 😊 **Happy** → Party, Upbeat, Dance  
   - 😢 **Sad** → Melancholy, Blues, Emotional  
   - 😡 **Angry** → Rock, Metal, Intense  
   - 😱 **Fear** → Ambient, Calm, Peaceful  
   - 😲 **Surprise** → Pop, Trending, Viral  
   - 😐 **Neutral** → Chill, Lo-fi, Focus  
4. **Playlist Search** – Queries Spotify for a matching playlist  
5. **Recommendation** – Opens the playlist in your default browser  
