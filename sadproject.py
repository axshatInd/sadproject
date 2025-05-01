import tkinter as tk
from tkinter import filedialog
import pygame
import os
import random
from mutagen.mp3 import MP3

MUSIC_FOLDER = "music"

class PlaylistIterator:
    def __init__(self, playlist):
        self.playlist = playlist
        self.index = 0

    def current(self):
        if not self.playlist:
            return None
        return self.playlist[self.index]

    def next(self):
        if self.playlist:
            self.index = (self.index + 1) % len(self.playlist)
            return self.current()

    def previous(self):
        if self.playlist:
            self.index = (self.index - 1) % len(self.playlist)
            return self.current()

    def set_index(self, idx):
        if 0 <= idx < len(self.playlist):
            self.index = idx

    def get_index(self):
        return self.index

    def shuffle(self):
        current_song = self.current()
        random.shuffle(self.playlist)
        if current_song in self.playlist:
            self.index = self.playlist.index(current_song)

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Player 🎵")
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        pygame.mixer.init()
        self.playlist = []
        self.iterator = PlaylistIterator(self.playlist)
        self.paused = False
        self.song_length = 0
        self.remaining_time = 0
        self.timer_id = None

        self.create_widgets()
        self.load_songs()

    def create_widgets(self):
        self.playlist_box = tk.Listbox(self.root, bg="black", fg="white", font=("Helvetica", 12), selectbackground="gray")
        self.playlist_box.pack(pady=10, fill=tk.BOTH, expand=True)
        self.playlist_box.bind("<Double-1>", self.play_selected_song)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, pady=5)

        # --- Left: Controls ---
        controls = tk.Frame(bottom_frame)
        controls.pack(side=tk.LEFT, padx=10)

        prev_btn = tk.Button(controls, text="⏮", command=self.prev_song, font=("Helvetica", 14))
        prev_btn.pack(side=tk.LEFT, padx=5)

        self.play_btn = tk.Button(controls, text="▶️", command=self.toggle_play_pause, font=("Helvetica", 14))
        self.play_btn.pack(side=tk.LEFT, padx=5)

        next_btn = tk.Button(controls, text="⏭", command=self.next_song, font=("Helvetica", 14))
        next_btn.pack(side=tk.LEFT, padx=5)

        # --- Center: Shuffle ---
        center_frame = tk.Frame(bottom_frame)
        center_frame.pack(side=tk.LEFT, expand=True)

        shuffle_btn = tk.Button(center_frame, text="🔀 Shuffle", command=self.shuffle_playlist, font=("Helvetica", 12))
        shuffle_btn.pack()

        # --- Right: Volume ---
        volume_frame = tk.Frame(bottom_frame)
        volume_frame.pack(side=tk.RIGHT, padx=10)

        tk.Label(volume_frame, text="Volume", font=("Helvetica", 10)).pack()
        self.volume_slider = tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_volume)
        self.volume_slider.set(70)
        self.volume_slider.pack()

        self.status_label = tk.Label(self.root, text="", font=("Helvetica", 10))
        self.status_label.pack(pady=5)

        self.time_label = tk.Label(self.root, text="Remaining: 00:00", font=("Helvetica", 10))
        self.time_label.pack(pady=2)

    def load_songs(self):
        if not os.path.exists(MUSIC_FOLDER):
            os.makedirs(MUSIC_FOLDER)
        self.playlist = [os.path.join(MUSIC_FOLDER, f) for f in os.listdir(MUSIC_FOLDER) if f.endswith('.mp3')]
        self.iterator = PlaylistIterator(self.playlist)

        self.playlist_box.delete(0, tk.END)
        for song in self.playlist:
            self.playlist_box.insert(tk.END, os.path.basename(song))

    def play_selected_song(self, event=None):
        selection = self.playlist_box.curselection()
        if selection:
            self.iterator.set_index(selection[0])
            self.play_song()

    def play_song(self):
        try:
            if self.timer_id:
                self.root.after_cancel(self.timer_id)

            song_path = self.iterator.current()
            if not song_path:
                return

            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            self.play_btn.config(text="⏸")
            self.paused = False

            audio = MP3(song_path)
            self.song_length = int(audio.info.length)
            self.remaining_time = self.song_length

            self.update_timer()

            index = self.iterator.get_index()
            self.playlist_box.selection_clear(0, tk.END)
            self.playlist_box.selection_set(index)
            self.playlist_box.see(index)
            self.status_label.config(text=f"Playing: {os.path.basename(song_path)}")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")

    def toggle_play_pause(self):
        if pygame.mixer.music.get_busy():
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.play_btn.config(text="⏸")
                self.update_timer()
            else:
                pygame.mixer.music.pause()
                self.paused = True
                self.play_btn.config(text="▶️")
                if self.timer_id:
                    self.root.after_cancel(self.timer_id)
        else:
            self.play_song()

    def next_song(self):
        self.iterator.next()
        self.play_song()

    def prev_song(self):
        self.iterator.previous()
        self.play_song()

    def shuffle_playlist(self):
        self.iterator.shuffle()
        self.playlist_box.delete(0, tk.END)
        for song in self.iterator.playlist:
            self.playlist_box.insert(tk.END, os.path.basename(song))
        self.status_label.config(text="Playlist shuffled")

    def set_volume(self, val):
        volume = float(val) / 100
        pygame.mixer.music.set_volume(volume)

    def update_timer(self):
        if not self.paused and pygame.mixer.music.get_busy() and self.remaining_time > 0:
            minutes = self.remaining_time // 60
            seconds = self.remaining_time % 60
            self.time_label.config(text=f"Remaining: {minutes:02}:{seconds:02}")
            self.remaining_time -= 1
            self.timer_id = self.root.after(1000, self.update_timer)
        else:
            self.time_label.config(text="Remaining: 00:00")

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()
