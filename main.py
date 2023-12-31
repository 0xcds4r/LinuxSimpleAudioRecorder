import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
import pyaudio
import wave
from threading import Thread
from datetime import datetime

class LocalizationConfig:
    def __init__(self):
        self.app_name = ""
        self.app_name_text = ""
        self.recorded_audio_title = ""
        self.timestamp_format = ""
        self.start_recording_btn_text = ""
        self.stop_recording_btn_text = ""
        self.format_label_text = ""
        self.channels_label_text = ""
        self.rate_label_text = ""
        self.filename_label_text = ""

    def load_config(self, file_path):
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    key, value = line.strip().split(' = ')
                    key = key.strip().replace('.', '_')  # Заменяем точки на подчеркивания
                    value = value.strip().strip('"')
                    setattr(self, key, value)
        except FileNotFoundError:
            print(f"File {file_path} not found.")
        except Exception as e:
            print(f"Error while file reading: {str(e)}")

    def display_config(self):
        print(f"{self.app_name_text} {self.app_name}")

config = LocalizationConfig()

# If u need russian language in app, then use locales-ru.txt
config_file_path = "./locales-en.txt"

config.load_config(config_file_path)
config.display_config() 

class AudioRecorderApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=config.app_name)
        self.set_border_width(10)

        timestamp = datetime.now().strftime(config.timestamp_format)
        self.filename = f"{config.recorded_audio_title}{timestamp}.wav"
        self.is_recording = False

        self.setup_gui()

    def setup_gui(self):
        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        self.add(grid)

        self.start_button = Gtk.Button.new_with_label(config.start_recording_btn_text)
        self.start_button.connect("clicked", self.start_recording)
        grid.attach(self.start_button, 0, 0, 1, 1)

        self.stop_button = Gtk.Button.new_with_label(config.stop_recording_btn_text)
        self.stop_button.connect("clicked", self.stop_recording)
        self.stop_button.set_sensitive(False)
        grid.attach(self.stop_button, 1, 0, 1, 1)

        label_format = Gtk.Label(config.format_label_text)
        grid.attach(label_format, 0, 1, 1, 1)

        self.format_combo = Gtk.ComboBoxText()
        self.format_combo.append_text("paInt16")
        self.format_combo.append_text("paInt32")
        self.format_combo.set_active(0)  # Default format: paInt16
        grid.attach(self.format_combo, 1, 1, 1, 1)

        label_channels = Gtk.Label(config.channels_label_text)
        grid.attach(label_channels, 0, 2, 1, 1)

        self.channels_combo = Gtk.ComboBoxText()
        self.channels_combo.append_text("1")
        self.channels_combo.append_text("2")
        self.channels_combo.set_active(0)  # Default channels: 1
        grid.attach(self.channels_combo, 1, 2, 1, 1)

        label_rate = Gtk.Label(config.rate_label_text)
        grid.attach(label_rate, 0, 3, 1, 1)

        self.rate_combo = Gtk.ComboBoxText()
        self.rate_combo.append_text("44100")
        self.rate_combo.append_text("22050")
        self.rate_combo.append_text("11025")
        self.rate_combo.set_active(0)  # Default rate: 44100
        grid.attach(self.rate_combo, 1, 3, 1, 1)

        label_filename = Gtk.Label(config.filename_label_text)
        grid.attach(label_filename, 0, 4, 1, 1)

        self.filename_entry = Gtk.Entry()
        # self.filename_entry.set_text(self.filename)  # Default filename
        grid.attach(self.filename_entry, 1, 4, 1, 1)

    def start_recording(self, button):
        self.is_recording = True
        timestamp = datetime.now().strftime(config.timestamp_format)
        custom_filename = self.filename_entry.get_text()
        self.filename = custom_filename if custom_filename else f"{config.recorded_audio_title}_{timestamp}.wav"
        self.start_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)

        self.recording_thread = Thread(target=self.record_audio_thread)
        self.recording_thread.start()

    def stop_recording(self, button):
        self.is_recording = False

    def record_audio_thread(self):
        CHUNK = 1024
        selected_format = self.format_combo.get_active_text()
        FORMAT = getattr(pyaudio, selected_format) if selected_format else pyaudio.paInt16
        CHANNELS = int(self.channels_combo.get_active_text())
        RATE = int(self.rate_combo.get_active_text())

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        frames = []
        while self.is_recording:
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        GObject.idle_add(self.reset_buttons)

    def reset_buttons(self):
        self.start_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)

if __name__ == "__main__":
    win = AudioRecorderApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
