import socket
import threading
import time
import pyttsx3
import re
from queue import Queue, Empty as QueueEmpty
import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import os
import sys

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = PYGAME_AVAILABLE
except ImportError:
    GTTS_AVAILABLE = False

try:
    import edge_tts
    import asyncio
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

class TwitchTTSBot:
    def __init__(self):
        self.server = 'irc.chat.twitch.tv'
        self.port = 6667
        self.nickname = 'justinfan12345'
        self.channel = ''
        
        self.sock = None
        self.running = False
        
        self.tts_engine = pyttsx3.init()
        self.tts_mode = "pyttsx3"
        self.current_voice = None
        self.tts_volume = 0.8
        
        if GTTS_AVAILABLE or EDGE_TTS_AVAILABLE:
            if PYGAME_AVAILABLE:
                try:
                    print("Próba inicjalizacji pygame.mixer...")
                    pygame.mixer.init()
                    if pygame.mixer.get_init():
                        print("Pygame mixer zainicjowany pomyślnie.")
                    else:
                        print("Pygame mixer NIE został zainicjowany po wywołaniu init().")
                except pygame.error as pg_error:
                    print(f"BŁĄD podczas inicjalizacji pygame.mixer: {pg_error}")
                    print("Odtwarzanie z gTTS/EdgeTTS może nie działać.")
                except Exception as e:
                    print(f"Nieoczekiwany błąd podczas inicjalizacji pygame.mixer: {e}")
                    print("Odtwarzanie z gTTS/EdgeTTS może nie działać.")
            else:
                print("Pygame nie jest dostępne, nie można zainicjować mixera.")
        
        self.setup_tts()
        
        self.tts_queue = Queue()
        
        self.setup_gui()
        
        self.tts_thread = None
        
        self.settings = self.load_settings()
        self.apply_settings()
        
    def setup_tts(self):
        voices = self.tts_engine.getProperty('voices')
        self.available_voices = []
        default_pyttsx3_voice_set = False
        
        if voices:
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': f"{voice.name} (System)",
                    'engine': 'pyttsx3'
                }
                self.available_voices.append(voice_info)
                if not default_pyttsx3_voice_set and any(keyword in voice.name.lower() for keyword in ['polish', 'polski', 'pl-pl']):
                    self.tts_engine.setProperty('voice', voice.id)
                    default_pyttsx3_voice_set = True
        
        if EDGE_TTS_AVAILABLE:
            edge_voices_data = [
                {'id': 'pl-PL-ZofiaNeural', 'name': 'Zofia (Microsoft Neural)', 'engine': 'edge'},
                {'id': 'pl-PL-MarekNeural', 'name': 'Marek (Microsoft Neural)', 'engine': 'edge'},
                {'id': 'pl-PL-AgnieszkaNeural', 'name': 'Agnieszka (Microsoft Neural)', 'engine': 'edge'},
            ]
            self.available_voices.extend(edge_voices_data)
        
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', self.tts_volume)

    def setup_gui(self):
        """Tworzenie interfejsu graficznego"""
        self.root = tk.Tk()
        self.root.title("Twitch TTS Bot (Tryb Prosty)")
        self.root.geometry("600x550")
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        connection_frame = ttk.LabelFrame(main_frame, text="Połączenie", padding=10)
        connection_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(connection_frame, text="Kanał Twitch:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.channel_entry = ttk.Entry(connection_frame, width=30)
        self.channel_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.connect_btn = ttk.Button(connection_frame, text="Połącz", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.clear_btn = ttk.Button(connection_frame, text="Wyczyść chat", command=self.clear_chat)
        self.clear_btn.grid(row=0, column=3, padx=5, pady=5)

        tts_settings_frame = ttk.LabelFrame(main_frame, text="Ustawienia TTS", padding=10)
        tts_settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(tts_settings_frame, text="Głos:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(tts_settings_frame, textvariable=self.voice_var, 
                                       values=[v['name'] for v in self.available_voices],
                                       state="readonly", width=40)
        self.voice_combo.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        self.voice_combo.bind('<<ComboboxSelected>>', self.on_voice_change)
        
        ttk.Label(tts_settings_frame, text="Szybkość mowy:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.speed_var = tk.IntVar(value=150)
        speed_scale = ttk.Scale(tts_settings_frame, from_=50, to=300, variable=self.speed_var, 
                               orient=tk.HORIZONTAL, command=self.update_tts_speed)
        speed_scale.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(tts_settings_frame, text="Głośność TTS:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.tts_volume_var = tk.DoubleVar(value=self.tts_volume)
        tts_volume_scale = ttk.Scale(tts_settings_frame, from_=0.0, to=1.0, variable=self.tts_volume_var,
                                  orient=tk.HORIZONTAL, command=self.update_tts_volume)
        tts_volume_scale.grid(row=2, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        
        self.read_nicknames = tk.BooleanVar(value=True)
        ttk.Checkbutton(tts_settings_frame, text="Czytaj nazwy użytkowników", 
                       variable=self.read_nicknames).grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        test_btn = ttk.Button(tts_settings_frame, text="Testuj Głos", command=self.test_voice)
        test_btn.grid(row=4, column=0, padx=5, pady=5)
        
        test_mode_btn = ttk.Button(tts_settings_frame, text="Tryb Testowy (wpisz wiadomość)", command=self.toggle_test_mode)
        test_mode_btn.grid(row=4, column=1, padx=5, pady=5)
        
        tts_settings_frame.columnconfigure(1, weight=1)
        
        simple_mode_info_frame = ttk.LabelFrame(main_frame, text="Informacja o trybie", padding=10)
        simple_mode_info_frame.pack(fill=tk.X, pady=10)
        info_label = ttk.Label(simple_mode_info_frame, 
                               text="TTS jest odtwarzany na domyślnym urządzeniu audio.\n"
                                    "Aby widzowie słyszeli TTS, upewnij się, że OBS (lub inny program do streamowania)\n"
                                    "przechwytuje 'Dźwięk z pulpitu' (Desktop Audio).",
                               justify=tk.LEFT)
        info_label.pack(pady=5, padx=5)


        chat_frame = ttk.LabelFrame(main_frame, text="Chat", padding=10)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=10, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        self.test_frame = ttk.Frame(chat_frame)
        test_label = ttk.Label(self.test_frame, text="Wpisz tekst do testu TTS:")
        test_label.pack(side=tk.LEFT, padx=(0,5))
        self.test_entry = ttk.Entry(self.test_frame, width=50)
        self.test_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.test_entry.bind('<Return>', self.send_test_message)
        test_send_btn = ttk.Button(self.test_frame, text="Mów", command=self.send_test_message)
        test_send_btn.pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value="Nie połączono")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.test_mode = False
    
    def update_tts_volume(self, value_str):
        """Aktualizacja głośności TTS"""
        self.tts_volume = float(value_str)
        if self.tts_mode == 'pyttsx3':
            self.tts_engine.setProperty('volume', self.tts_volume)

    def play_audio_file_pygame(self, audio_file, volume=1.0, is_temp_file=True):
        """Odtwórz plik audio używając pygame i usuń go, jeśli tymczasowy."""
        if not pygame.mixer.get_init():
            print("Pygame mixer nie jest zainicjowany. Nie można odtworzyć pliku.")
            if is_temp_file and os.path.exists(audio_file):
                 try: os.remove(audio_file)
                 except: pass
            return
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception as e:
            print(f"Błąd odtwarzania audio z pygame ({audio_file}): {e}")
        finally:
            if is_temp_file and os.path.exists(audio_file):
                try:
                    if pygame.mixer.music.get_busy(): pygame.mixer.music.stop()
                    time.sleep(0.1)
                    os.remove(audio_file)
                except PermissionError:
                    print(f"Nie można usunąć pliku tymczasowego (PermissionError): {audio_file}.")
                except Exception as e_del:
                    print(f"Nie można usunąć pliku tymczasowego {audio_file}: {e_del}")
    
    def load_settings(self):
        """Wczytanie ustawień z pliku"""
        try:
            if os.path.exists('tts_settings_simple.json'):
                with open('tts_settings_simple.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Błąd wczytywania ustawień: {e}")
        return {}
    
    def save_settings(self):
        """Zapisanie ustawień do pliku"""
        settings = {
            'channel': self.channel_entry.get(),
            'speed': self.speed_var.get(),
            'tts_volume': self.tts_volume_var.get(),
            'read_nicknames': self.read_nicknames.get(),
            'voice': self.voice_var.get(),
        }
        try:
            with open('tts_settings_simple.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Błąd zapisywania ustawień: {e}")
    
    def apply_settings(self):
        """Zastosowanie zapisanych ustawień"""
        if 'channel' in self.settings:
            self.channel_entry.insert(0, self.settings['channel'])
        if 'speed' in self.settings:
            self.speed_var.set(self.settings['speed'])
            self.update_tts_speed(self.settings['speed']) 
        
        if 'tts_volume' in self.settings:
            self.tts_volume_var.set(self.settings['tts_volume'])
        self.update_tts_volume(self.tts_volume_var.get())

        if 'read_nicknames' in self.settings:
            self.read_nicknames.set(self.settings['read_nicknames'])
        
        if 'voice' in self.settings and self.settings['voice']:
            self.voice_var.set(self.settings['voice'])
        elif self.available_voices:
            default_edge_voice = next((v for v in self.available_voices if v['engine'] == 'edge' and 'Zofia' in v['name']), None)
            if default_edge_voice:
                self.voice_var.set(default_edge_voice['name'])
            else:
                first_polish_system = next((v for v in self.available_voices if v['engine'] == 'pyttsx3' and any(k in v['name'].lower() for k in ['polish', 'polski'])), None)
                if first_polish_system:
                    self.voice_var.set(first_polish_system['name'])
                elif self.available_voices:
                     self.voice_var.set(self.available_voices[0]['name'])
        self.on_voice_change()

    def on_voice_change(self, event=None):
        """Obsługa zmiany głosu"""
        selected_name = self.voice_var.get()
        for voice in self.available_voices:
            if voice['name'] == selected_name:
                self.current_voice = voice['id']
                self.tts_mode = voice['engine']
                if voice['engine'] == 'pyttsx3':
                    self.tts_engine.setProperty('voice', voice['id'])
                    self.tts_engine.setProperty('volume', self.tts_volume_var.get())
                break
    
    def toggle_test_mode(self):
        """Przełączanie trybu testowego"""
        self.test_mode = not self.test_mode
        if self.test_mode:
            self.test_frame.pack(fill=tk.X, pady=(5,0), side=tk.BOTTOM)
            self.status_var.set("Tryb testowy - wpisz wiadomość powyżej czatu i naciśnij Mów")
        else:
            self.test_frame.pack_forget()
            self.status_var.set("Nie połączono" if not self.running else f"Połączono z #{self.channel}")
    
    def test_voice(self):
        """Test wybranego głosu"""
        test_text = "Cześć! To jest test głosu dla bota Twitch TTS."
        if self.test_mode:
             self.add_to_chat("Tester", test_text)
        else:
            self.tts_queue.put(test_text)
            if not self.running and (not self.tts_thread or not self.tts_thread.is_alive()):
                temp_tts_thread = threading.Thread(target=self.tts_worker_single_run, daemon=True)
                temp_tts_thread.start()
                self.status_var.set("Testowanie głosu...")


    def tts_worker_single_run(self):
        """Uruchamia kolejkę TTS dla pojedynczych zadań, gdy nie jest połączony."""
        if not self.tts_queue.empty():
            text_to_speak = self.tts_queue.get()
            self._process_tts_text(text_to_speak)
            self.tts_queue.task_done()
        if self.status_var.get() == "Testowanie głosu...":
             self.status_var.set("Nie połączono")


    async def speak_with_edge_tts(self, text, voice_id):
        """Mówienie za pomocą Edge TTS, odtwarzanie przez pygame na domyślnym urządzeniu."""
        if not EDGE_TTS_AVAILABLE or not pygame.mixer.get_init():
            print("Edge TTS lub Pygame mixer nie są dostępne/zainicjowane. Używam pyttsx3 jako fallback.")
            self.speak_with_pyttsx3(text)
            return

        temp_audio_file = f"temp_edge_tts_{time.time_ns()}.mp3"
        try:
            rate_percentage = int((self.speed_var.get() / 150.0 - 1.0) * 75.0)
            rate_str = f"{'+' if rate_percentage >= 0 else ''}{rate_percentage}%"
            
            communicate = edge_tts.Communicate(text, voice_id, rate=rate_str)
            await communicate.save(temp_audio_file)
            
            self.play_audio_file_pygame(temp_audio_file, self.tts_volume_var.get(), is_temp_file=True)
                        
        except Exception as e:
            print(f"Błąd Edge TTS: {e}")
            if os.path.exists(temp_audio_file):
                try: os.remove(temp_audio_file)
                except: pass
    
    def update_tts_speed(self, value_str):
        """Aktualizacja szybkości TTS"""
        rate = int(float(value_str))
        self.tts_engine.setProperty('rate', rate)
    
    def clean_message(self, message):
        """Czyszczenie wiadomości z emotek i niepotrzebnych znaków"""
        message = re.sub(r':\w+:', '', message)
        message = re.sub(r'http[s]?://\S+', 'link', message)
        message = re.sub(r'\s+', ' ', message).strip()
        return message
    
    def add_to_chat(self, username, message):
        """Dodanie wiadomości do okna czatu i kolejki TTS"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{username}: {message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        clean_msg = self.clean_message(message)
        if clean_msg:
            tts_text = f"{username} mówi: {clean_msg}" if self.read_nicknames.get() else clean_msg
            self.tts_queue.put(tts_text)
    
    def _process_tts_text(self, text):
        """Wewnętrzna funkcja do przetwarzania pojedynczego tekstu TTS."""
        current_engine_mode = self.tts_mode
        
        if current_engine_mode == 'edge' and EDGE_TTS_AVAILABLE:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if self.current_voice:
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.speak_with_edge_tts(text, self.current_voice), loop)
                else:
                    loop.run_until_complete(self.speak_with_edge_tts(text, self.current_voice))
            else:
                print("Brak wybranego głosu dla Edge TTS.")
        
        elif current_engine_mode == 'pyttsx3':
            self.speak_with_pyttsx3(text)
            
        elif current_engine_mode == 'gtts' and GTTS_AVAILABLE:
             self.speak_with_gtts(text)

        else:
            print(f"Tryb TTS '{current_engine_mode}' nie jest w pełni obsługiwany lub wystąpił błąd. Używam pyttsx3 jako fallback.")
            self.speak_with_pyttsx3(text)


    def tts_worker(self):
        """Wątek obsługujący TTS z kolejki."""
        if EDGE_TTS_AVAILABLE:
            try:
                loop = asyncio.get_event_loop_policy().get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        while self.running:
            try:
                text_to_speak = self.tts_queue.get(timeout=1)
                self._process_tts_text(text_to_speak)
                self.tts_queue.task_done()
            except QueueEmpty:
                continue
            except Exception as e:
                print(f"Błąd w wątku TTS: {e}")
                continue
    
    def speak_with_pyttsx3(self, text):
        """Mówienie za pomocą pyttsx3 na domyślnym urządzeniu."""
        try:
            self.tts_engine.setProperty('volume', self.tts_volume_var.get())
            self.tts_engine.setProperty('rate', self.speed_var.get())
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Błąd pyttsx3: {e}")
    
    def speak_with_gtts(self, text):
        """Mówienie za pomocą gTTS, odtwarzanie przez pygame na domyślnym urządzeniu."""
        if not GTTS_AVAILABLE or not pygame.mixer.get_init():
            print("gTTS lub Pygame mixer nie są dostępne/zainicjowane. Używam pyttsx3 jako fallback.")
            self.speak_with_pyttsx3(text)
            return
        
        temp_gtts_file = f"temp_gtts_{time.time_ns()}.mp3"
        try:
            is_slow = self.speed_var.get() < 120 
            tts_obj = gTTS(text=text, lang='pl', slow=is_slow)
            tts_obj.save(temp_gtts_file)
            
            self.play_audio_file_pygame(temp_gtts_file, self.tts_volume_var.get(), is_temp_file=True)

        except Exception as e:
            print(f"Błąd gTTS: {e}")
            if os.path.exists(temp_gtts_file):
                try: os.remove(temp_gtts_file)
                except: pass
    
    def connect_to_twitch(self):
        """Połączenie z czatem Twitch"""
        try:
            self.sock = socket.socket()
            self.sock.connect((self.server, self.port))
            
            self.sock.send(f"PASS SCHMOOPIIE\n".encode('utf-8'))
            self.sock.send(f"NICK {self.nickname}\n".encode('utf-8'))
            self.sock.send(f"JOIN #{self.channel}\n".encode('utf-8'))
            self.sock.send("CAP REQ :twitch.tv/tags\n".encode('utf-8'))
            self.sock.send("CAP REQ :twitch.tv/commands\n".encode('utf-8'))
            
            self.running = True
            self.status_var.set(f"Połączono z #{self.channel}")
            
            if not self.tts_thread or not self.tts_thread.is_alive():
                self.tts_thread = threading.Thread(target=self.tts_worker, daemon=True)
                self.tts_thread.start()
            
            chat_thread = threading.Thread(target=self.listen_to_chat, daemon=True)
            chat_thread.start()
            
            return True
            
        except Exception as e:
            self.status_var.set(f"Błąd połączenia: {str(e)}")
            return False
    
    def listen_to_chat(self):
        """Nasłuchiwanie wiadomości z czatu"""
        buffer = ""
        while self.running:
            try:
                chunk = self.sock.recv(2048).decode('utf-8', errors='ignore')
                if not chunk:
                    if self.running:
                        self.status_var.set("Połączenie z serwerem Twitch zostało przerwane.")
                        self.root.after(0, self.disconnect)
                    break 

                buffer += chunk
                messages = buffer.split("\r\n")
                buffer = messages.pop()

                for line in messages:
                    if not self.running: break

                    if line.startswith('PING'):
                        self.sock.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                    elif 'PRIVMSG' in line:
                        match = re.match(r"(?:@(?P<tags>[^\s]+) )?:(?P<username>[^!]+)![^ ]+ PRIVMSG #\S+ :(?P<message>.+)", line)
                        if match:
                            username = match.group('username')
                            message = match.group('message')
                            self.root.after(0, self.add_to_chat, username, message)
            except socket.timeout:
                 continue
            except ConnectionAbortedError:
                if self.running: self.status_var.set("Połączenie przerwane (aborted).")
                break
            except ConnectionResetError:
                if self.running: self.status_var.set("Połączenie zresetowane przez serwer.")
                break
            except Exception as e:
                if self.running:
                    print(f"Błąd w nasłuchiwaniu czatu: {e}")
                break 
        
        if self.running:
            self.root.after(0, self.disconnect)


    def disconnect(self):
        """Rozłączenie z czatem"""
        self.running = False 
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR) 
                self.sock.close()
            except Exception as e:
                print(f"Błąd podczas zamykania socketa: {e}")
            finally:
                self.sock = None
        
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except QueueEmpty:
                break
        
        self.status_var.set("Rozłączono")
        self.connect_btn.config(text="Połącz") 
    
    def toggle_connection(self):
        """Przełączanie połączenia"""
        if not self.running:
            channel_name = self.channel_entry.get().strip()
            if not channel_name:
                self.status_var.set("Wprowadź nazwę kanału!")
                return
            
            self.channel = channel_name.lower()
            if self.connect_to_twitch():
                self.connect_btn.config(text="Rozłącz")
                self.save_settings() 
        else:
            self.disconnect()
    
    def clear_chat(self):
        """Wyczyszczenie okna czatu"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def send_test_message(self, event=None): 
        """Wysyła wiadomość testową do czatu i TTS"""
        test_text = self.test_entry.get()
        if test_text:
            self.add_to_chat("Tester", test_text) 
            self.test_entry.delete(0, tk.END)
    
    def run(self):
        """Uruchomienie aplikacji"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Obsługa zamknięcia aplikacji"""
        self.save_settings()
        if self.running:
            self.disconnect()
        
        if pygame.mixer.get_init():
            pygame.mixer.quit()
            
        self.root.destroy()

if __name__ == "__main__":
    print("=" * 60)
    print("🎮 Twitch TTS Bot - Tryb Prosty 🎮")
    print("=" * 60)
    print("Ten bot odtwarza TTS na domyślnym urządzeniu audio.")
    print("Aby widzowie słyszeli TTS, OBS/program do streamowania musi")
    print("przechwytywać 'Dźwięk z pulpitu' (Desktop Audio).")
    
    print("\n🔍 Sprawdzanie wymaganych bibliotek...")
    lib_status = []
    try: import pyttsx3; lib_status.append("✓ pyttsx3 (Podstawowy TTS)")
    except ImportError: lib_status.append("✗ pyttsx3 (Podstawowy TTS) - WYMAGANY"); sys.exit("Brak pyttsx3")

    if GTTS_AVAILABLE: lib_status.append("✓ gTTS & pygame (Google TTS + odtwarzacz)")
    else: lib_status.append("✗ gTTS lub pygame (Opcjonalny Google TTS) - gTTS nie będzie działać")
    
    if EDGE_TTS_AVAILABLE: lib_status.append("✓ edge-tts (Microsoft Neural Voices)")
    else: lib_status.append("✗ edge-tts (Microsoft Neural Voices) - brak najlepszych głosów")
    
    if not pygame.mixer.get_init() and (GTTS_AVAILABLE or EDGE_TTS_AVAILABLE):
        lib_status.append("✗ pygame.mixer nie zainicjowany - głosy gTTS/Edge mogą nie działać poprawnie.")


    for status in lib_status: print(status)

    missing_critical_pygame_functionality = (GTTS_AVAILABLE or EDGE_TTS_AVAILABLE) and (not PYGAME_AVAILABLE or (PYGAME_AVAILABLE and not pygame.mixer.get_init()))

    if not EDGE_TTS_AVAILABLE or missing_critical_pygame_functionality:
        print("\n⚠️  Dla najlepszych wrażeń, zalecana instalacja/konfiguracja:")
        if not EDGE_TTS_AVAILABLE: print("   - pip install edge-tts (dla wysokiej jakości głosów Microsoft)")
        if missing_critical_pygame_functionality:
            if not PYGAME_AVAILABLE:
                print("   - pip install pygame (dla odtwarzania głosów gTTS/EdgeTTS)")
            elif PYGAME_AVAILABLE and not pygame.mixer.get_init():
                 print("   - pygame.mixer nie został poprawnie zainicjowany. Sprawdź konfigurację audio/SDL.")
        print("   Bot będzie próbował działać z dostępnymi opcjami.")


    print("\n🚀 Uruchamianie bota...")
    
    if sys.platform == "win32" and EDGE_TTS_AVAILABLE:
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception as e_policy:
            print(f"Ostrzeżenie: Nie udało się ustawić polityki pętli asyncio dla Windows: {e_policy}")

    try:
        bot = TwitchTTSBot()
        bot.run()
    except Exception as e:
        print(f"\n💥 Krytyczny błąd podczas uruchamiania lub działania aplikacji: {e}")
        import traceback
        traceback.print_exc()
        input("Naciśnij Enter, aby zamknąć...")