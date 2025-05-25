![](https://i.imgur.com/NEVwXnd.png)

# Twitch TTS Bot (Tryb Prosty) - Dokumentacja

## Spis Treści
1. [Wprowadzenie](#wprowadzenie)
2. [Funkcje](#funkcje)
3. [Wymagania Systemowe i Instalacja](#wymagania-systemowe-i-instalacja)
   - [Python](#python)
   - [Biblioteki (pip)](#biblioteki-pip)
4. [Uruchamianie Programu](#uruchamianie-programu)
5. [Interfejs Użytkownika (GUI)](#interfejs-użytkownika-gui)
   - [Sekcja Połączenia](#sekcja-połączenia)
   - [Sekcja Ustawień TTS](#sekcja-ustawień-tts)
   - [Informacja o Trybie](#informacja-o-trybie)
   - [Sekcja Czatu](#sekcja-czatu)
   - [Pasek Statusu](#pasek-statusu)
6. [Jak Działa TTS na Streamie?](#jak-działa-tts-na-streamie)
7. [Wybór Głosów](#wybór-głosów)
8. [Zapisywanie Ustawień](#zapisywanie-ustawień)
9. [Struktura Kodu (Ogólny Zarys)](#struktura-kodu-ogólny-zarys)
   - [Główne Moduły](#główne-moduły)
   - [Klasa `TwitchTTSBot`](#klasa-twitchttsbot)
10. [Rozwiązywanie Problemów](#rozwiązywanie-problemów)
11. [Możliwe Rozszerzenia](#możliwe-rozszerzenia)

---

## 1. Wprowadzenie

**Twitch TTS Bot (Tryb Prosty)** to aplikacja napisana w Pythonie, która łączy się z czatem Twitch i odczytuje wiadomości na głos przy użyciu syntezy mowy (Text-To-Speech, TTS). Została zaprojektowana z myślą o prostocie: TTS jest odtwarzany na domyślnym urządzeniu audio streamera, co pozwala widzom słyszeć go, jeśli streamer przechwytuje dźwięk z pulpitu w swoim oprogramowaniu do streamowania (np. OBS Studio, Streamlabs).

Ten tryb eliminuje potrzebę konfiguracji wirtualnych kabli audio (np. Virtual Audio Cable).

## 2. Funkcje

- **Połączenie z czatem Twitch:** Łączy się z wybranym kanałem Twitch jako anonimowy użytkownik.
- **Odczytywanie wiadomości:** Przetwarza wiadomości z czatu i odczytuje je na głos.
- **Wybór silnika TTS i głosu:**
  - Obsługa systemowych głosów TTS przez `pyttsx3`.
  - Obsługa wysokiej jakości głosów Microsoft Neural (np. Zofia, Marek) przez `edge-tts`.
  - Opcjonalna obsługa głosów Google przez `gTTS`.
- **Konfiguracja TTS:** Możliwość dostosowania szybkości mowy i głośności TTS.
- **Czytanie nicków:** Opcja włączenia/wyłączenia odczytywania nazwy użytkownika przed wiadomością.
- **Interfejs graficzny (GUI):** Prosty i intuicyjny interfejs oparty na `tkinter` do zarządzania połączeniem i ustawieniami.
- **Wyświetlanie czatu:** Wbudowane okno czatu pokazujące przychodzące wiadomości.
- **Tryb testowy:** Możliwość wpisania własnego tekstu i przetestowania działania TTS.
- **Zapisywanie ustawień:** Ustawienia użytkownika (kanał, głos, szybkość, głośność) są zapisywane w pliku `tts_settings_simple.json` i automatycznie wczytywane przy ponownym uruchomieniu.
- **Czyszczenie wiadomości:** Usuwanie linków i emotikon Twitcha przed przekazaniem tekstu do silnika TTS.

## 3. Wymagania Systemowe i Instalacja

### Python
- Python 3.8 lub nowszy.

### Biblioteki (pip)
Aby program działał poprawnie, należy zainstalować następujące biblioteki Pythona za pomocą `pip`. Otwórz terminal lub wiersz poleceń i wykonaj:

**Wymagane podstawowe:**
```bash
pip install pyttsx3
```

**Zalecane dla lepszych głosów i odtwarzania (mocno rekomendowane):**
```bash
pip install edge-tts pygame
```

- `edge-tts`: Dla wysokiej jakości głosów Microsoft Neural.
- `pygame`: Używane do odtwarzania plików audio generowanych przez edge-tts i gTTS.

**Opcjonalne (jeśli chcesz używać głosów Google):**
```bash
pip install gTTS
```

**Pełna instalacja zalecanych i opcjonalnych bibliotek:**
```bash
pip install pyttsx3 edge-tts pygame gTTS
```

## 4. Uruchamianie Programu

1. Upewnij się, że masz zainstalowany Python i wszystkie wymagane biblioteki (patrz sekcja Instalacja).
2. Zapisz kod programu jako plik `.py` (np. `twitch_tts.py`).
3. Otwórz terminal lub wiersz poleceń w folderze, w którym zapisałeś plik.
4. Uruchom program komendą:

```bash
python twitch_tts.py
```

lub (jeśli używasz konkretnej wersji Pythona lub Python Launcher w Windows):

```bash
py twitch_tts.py
```

lub np.:

```bash
python3.11 twitch_tts.py
```

## 5. Interfejs Użytkownika (GUI)

Po uruchomieniu programu pojawi się główne okno aplikacji z kilkoma sekcjami:

### Sekcja Połączenia

- **Kanał Twitch:** Pole tekstowe, w którym należy wpisać nazwę kanału Twitch, z którym chcesz się połączyć (np. `nazwa_twojego_kanalu`).
- **Połącz/Rozłącz:** Przycisk do nawiązywania i przerywania połączenia z czatem Twitch.
- **Wyczyść chat:** Przycisk do wyczyszczenia zawartości okna czatu w aplikacji.

### Sekcja Ustawień TTS

- **Głos:** Rozwijana lista (Combobox) pozwalająca wybrać dostępny głos TTS. Głosy są pobierane z systemu (pyttsx3), Microsoft (edge-tts) oraz opcjonalnie Google (gTTS).
- **Szybkość mowy:** Suwak do regulacji szybkości, z jaką odczytywane są wiadomości.
- **Głośność TTS:** Suwak do regulacji głośności syntezatora mowy. Ta głośność będzie słyszalna zarówno dla streamera, jak i (pośrednio) dla widzów.
- **Czytaj nazwy użytkowników:** Pole wyboru (Checkbox) decydujące, czy przed każdą wiadomością ma być odczytana nazwa użytkownika, który ją wysłał (np. "Użytkownik123 mówi: Cześć!").
- **Testuj Głos:** Przycisk do odtworzenia przykładowej frazy wybranym głosem i ustawieniami.
- **Tryb Testowy (wpisz wiadomość):** Przycisk, który po kliknięciu wyświetla poniżej okna czatu dodatkowe pole. Umożliwia ono wpisanie własnego tekstu, który po naciśnięciu "Mów" lub Enter zostanie przetworzony przez TTS.

### Informacja o Trybie

Ta sekcja wyświetla stałą informację przypominającą, że TTS jest odtwarzany na domyślnym urządzeniu audio i aby był słyszalny na streamie, oprogramowanie do streamowania musi przechwytywać dźwięk z pulpitu.

### Sekcja Czatu

- **Okno czatu:** Duże pole tekstowe (ScrolledText), w którym wyświetlane są wiadomości przychodzące z czatu Twitch.
- **Pole testowe (ukryte domyślnie):** Po kliknięciu "Tryb Testowy", pod oknem czatu pojawia się pole do wprowadzania tekstu i przycisk "Mów" do testowania TTS.

### Pasek Statusu

Na samym dole okna znajduje się pasek statusu, który wyświetla aktualny stan połączenia (np. "Nie połączono", "Połączono z #kanał", "Błąd połączenia").

## 6. Jak Działa TTS na Streamie?

W tym "Trybie Prostym":

1. Aplikacja Twitch TTS Bot odtwarza dźwięk syntezatora mowy na domyślnym urządzeniu wyjściowym audio Twojego komputera (np. na słuchawkach lub głośnikach, których używasz).
2. Ty (streamer) słyszysz TTS bezpośrednio z tego urządzenia.
3. Twoje oprogramowanie do streamowania (np. OBS Studio, Streamlabs) musi być skonfigurowane tak, aby przechwytywało dźwięk z pulpitu (często nazywane "Desktop Audio" lub "Dźwięk systemowy").
4. Ponieważ TTS jest częścią dźwięku z pulpitu, widzowie również go usłyszą razem z innymi dźwiękami z Twojego komputera (np. dźwiękiem z gry, muzyką).

**Zalety:**
- Prosta konfiguracja, nie wymaga dodatkowego oprogramowania (jak Virtual Audio Cable).

**Wady:**
- Brak możliwości niezależnej regulacji głośności TTS dla widzów z poziomu aplikacji bota (głośność dla widzów zależy od głośności TTS w bocie oraz od ustawień źródła "Dźwięk z pulpitu" w OBS).
- TTS jest zmiksowany z innymi dźwiękami pulpitu.

## 7. Wybór Głosów

Program automatycznie wykrywa dostępne głosy:

- **Systemowe (pyttsx3):** Głosy zainstalowane w Twoim systemie operacyjnym. Ich jakość i dostępność (w tym polskie) mogą się różnić.
- **Microsoft Neural (edge-tts):** Wysokiej jakości głosy, w tym bardzo dobre polskie (Zofia, Marek, Agnieszka). Zalecane dla najlepszej jakości. Wymagają zainstalowanej biblioteki `edge-tts` i `pygame`.
- **Google (gTTS):** Głosy od Google. Wymagają zainstalowanej biblioteki `gTTS` i `pygame`.

Głosy można wybrać z rozwijanej listy w sekcji "Ustawienia TTS".

## 8. Zapisywanie Ustawień

Po zmianie ustawień (takich jak wybrany kanał, głos, szybkość mowy, głośność) i udanym połączeniu z kanałem, ustawienia są automatycznie zapisywane do pliku `tts_settings_simple.json` w tym samym folderze co program. Przy następnym uruchomieniu programu, te ustawienia zostaną automatycznie wczytane.

## 9. Struktura Kodu (Ogólny Zarys)

### Główne Moduły

Program wykorzystuje standardowe moduły Pythona oraz biblioteki zewnętrzne:

- `socket`: Do komunikacji sieciowej z serwerem IRC Twitcha.
- `threading`: Do obsługi operacji sieciowych i TTS w osobnych wątkach, aby nie blokować interfejsu GUI.
- `time`: Do obsługi opóźnień.
- `pyttsx3`, `edge_tts`, `gTTS`: Silniki syntezy mowy.
- `pygame`: Do odtwarzania plików audio generowanych przez edge-tts i gTTS.
- `re`: Do wyrażeń regularnych (np. czyszczenie wiadomości).
- `queue`: Do bezpiecznego przekazywania wiadomości między wątkami (kolejka TTS).
- `tkinter`: Do tworzenia interfejsu graficznego.
- `json`: Do zapisywania i wczytywania ustawień.
- `os`: Do operacji na systemie plików (np. sprawdzanie istnienia pliku ustawień).
- `sys`: Do interakcji z interpreterem Pythona.
- `asyncio`: Używane wewnętrznie przez edge-tts.

### Klasa `TwitchTTSBot`

Główna logika programu jest zamknięta w klasie `TwitchTTSBot`. Najważniejsze metody:

- `__init__(self)`: Konstruktor, inicjalizuje zmienne, silniki TTS, GUI, wczytuje ustawienia.
- `setup_tts(self)`: Konfiguruje dostępne głosy.
- `setup_gui(self)`: Tworzy wszystkie elementy interfejsu graficznego.
- `connect_to_twitch(self)`: Nawiązuje połączenie z serwerem IRC Twitcha.
- `listen_to_chat(self)`: Wątek nasłuchujący wiadomości z czatu.
- `add_to_chat(self, username, message)`: Dodaje wiadomość do GUI i kolejki TTS.
- `_process_tts_text(self, text)`: Wybiera odpowiedni silnik TTS i odczytuje tekst.
- `tts_worker(self)`: Wątek przetwarzający kolejkę wiadomości do odczytania.
- `speak_with_pyttsx3(self, text)`, `speak_with_edge_tts(self, text, voice_id)`, `speak_with_gtts(self, text)`: Metody specyficzne dla każdego silnika TTS.
- `play_audio_file_pygame(self, audio_file, volume, is_temp_file)`: Odtwarza plik audio za pomocą pygame.
- `save_settings(self)`, `load_settings(self)`, `apply_settings(self)`: Zarządzanie ustawieniami.
- Metody obsługi zdarzeń GUI (np. kliknięcia przycisków, zmiany wartości suwaków).
- `run(self)`: Uruchamia główną pętlę aplikacji tkinter.
- `on_closing(self)`: Obsługa zamknięcia okna aplikacji.

## 10. Rozwiązywanie Problemów

**ModuleNotFoundError:** Oznacza brak wymaganej biblioteki. Zainstaluj ją używając `pip install <nazwa_biblioteki>`.

**Brak polskich głosów / niska jakość głosu:**
- Upewnij się, że masz zainstalowane `edge-tts` i `pygame`.
- Wybierz głos z dopiskiem "(Microsoft Neural)" z listy głosów (np. Zofia, Marek).
- Sprawdź, czy w Twoim systemie są zainstalowane polskie pakiety językowe i głosy systemowe.

**TTS nie działa / brak dźwięku:**
- Sprawdź, czy głośność TTS w aplikacji nie jest ustawiona na 0.
- Upewnij się, że domyślne urządzenie audio w systemie działa poprawnie i nie jest wyciszone.
- Jeśli używasz edge-tts lub gTTS, sprawdź, czy pygame.mixer inicjuje się poprawnie (komunikaty w konsoli przy starcie programu mogą pomóc). Błędy inicjalizacji pygame.mixer często wskazują na problemy z konfiguracją SDL lub sterownikami audio.
- Sprawdź komunikaty błędów w konsoli, z której uruchomiłeś program.

**Program się nie łączy z Twitchem:**
- Sprawdź poprawność nazwy kanału Twitch.
- Upewnij się, że masz połączenie z internetem.
- Sprawdź, czy zapora sieciowa nie blokuje połączenia.

**AttributeError: type object 'Queue' has no attribute 'Empty':** Upewnij się, że wyjątek Empty jest poprawnie importowany z modułu queue (`from queue import Queue, Empty as QueueEmpty`) i używany w blokach try-except (`except QueueEmpty:`).

**Ostrzeżenie DeprecationWarning: There is no current event loop (asyncio):** Zwykle nie jest to krytyczny błąd, ale wskazuje na starszy sposób użycia `asyncio.get_event_loop()`. Kod próbuje sobie z tym radzić.

## 11. Możliwe Rozszerzenia

- Dodanie obsługi tokenu OAuth dla logowania jako konkretny użytkownik (umożliwiłoby to np. wysyłanie wiadomości przez bota).
- Filtrowanie wiadomości (np. blokowanie określonych słów, ignorowanie komend botów).
- Kolejkowanie TTS z priorytetami (np. dla subskrybentów).
- Integracja z systemem punktów kanału Twitch.
- Bardziej zaawansowane opcje czyszczenia wiadomości (np. usuwanie powtórzeń znaków).
- Wprowadzenie ponownie "Trybu Zaawansowanego" z obsługą Virtual Audio Cable dla bardziej precyzyjnej kontroli dźwięku.
