import socket
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
import datetime
import os
import locale

# i18n Vorbereitung
def _(text):
    """Einfache Übersetzungsfunktion - kann später durch gettext ersetzt werden"""
    return text

# Übersetzungen (können später in separate Dateien ausgelagert werden)
TRANSLATIONS = {
    'de': {
        'title': 'LightBurn zu LinuxCNC Bridge (l2l)',
        'status': 'Status:',
        'initializing': 'Initialisiere...',
        'waiting_connection': 'Warte auf Verbindung',
        'connected': 'Verbunden mit',
        'connection_lost': 'Verbindung getrennt',
        'error': 'Fehler:',
        'receiving_program': 'Empfange Programm...',
        'program_received': 'Programm empfangen',
        'backup_create': 'Backup erstellen',
        'current_program': 'Aktuelles Programm',
        'close': 'Schließen',
        'quit': 'Beenden',
        'gcode_communication': 'G-Code Kommunikation:',
        'backup_created': 'Backup erstellt:',
        'no_program_file': 'Keine Programmdatei vorhanden',
        'backup_error': 'Fehler beim Erstellen der Backup-Datei:',
        'quitting': 'Beende Programm...',
    },
    'en': {
        'title': 'LightBurn to LinuxCNC Bridge (l2l)',
        'status': 'Status:',
        'initializing': 'Initializing...',
        'waiting_connection': 'Waiting for connection',
        'connected': 'Connected to',
        'connection_lost': 'Connection lost',
        'error': 'Error:',
        'receiving_program': 'Receiving program...',
        'program_received': 'Program received',
        'backup_create': 'Create backup',
        'current_program': 'Current program',
        'close': 'Close',
        'quit': 'Quit',
        'gcode_communication': 'G-Code Communication:',
        'backup_created': 'Backup created:',
        'no_program_file': 'No program file available',
        'backup_error': 'Error creating backup file:',
        'quitting': 'Quitting program...',
    }
}

# Aktuelle Sprache (kann später aus Konfiguration gelesen werden)
CURRENT_LANG = 'de'

def get_text(key):
    """Holt den übersetzten Text für den aktuellen Schlüssel"""
    return TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS['en']).get(key, key)



# Konfiguration
HOST = '0.0.0.0'
PORT = 23
LOG_FILE = "lightburn_log.txt"
PROGRAM_FILE = "lightburn_program.ngc"

class GCodeServer:
    def __init__(self, gui_callback, gui_quit, status_callback, program_status_callback):
        self.gui_callback = gui_callback
        self.gui_quit = gui_quit
        self.status_callback = status_callback
        self.program_status_callback = program_status_callback
        self.running = True
        self.connected = False
        self.receiving_program = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Port wiederverwendbar machen
        self.server.settimeout(1.0)
        self.thread = threading.Thread(target=self.run_server, daemon=True)
        self.thread.start()

    def run_server(self):
        try:
            self.server.bind((HOST, PORT))
            self.server.listen(1)
            self.gui_callback(f"[TCP] {get_text('waiting_connection')} auf {HOST}:{PORT} ...")
            self.status_callback(get_text('waiting_connection'), "yellow")
            while self.running:
                try:
                    self.conn, self.addr = self.server.accept()
                    self.connected = True
                    self.gui_callback(f"[TCP] {get_text('connected')} {self.addr}")
                    self.status_callback(f"{get_text('connected')} {self.addr[0]}", "green")
                    self.conn.settimeout(1.0)
                    self.conn.sendall(b"Grbl 1.1f ['$' for help]\r\n")
                    self.gui_callback("→ Grbl 1.1f ['$' for help]")
                    self.handle_connection()
                except socket.timeout:
                    continue
        except Exception as e:
            self.gui_callback(f"[{get_text('error')}] {e}")
            self.status_callback(f"{get_text('error')} {e}", "red")
        finally:
            self.stop()

    def handle_connection(self):
        with open(LOG_FILE, "a") as log, open(PROGRAM_FILE, "w") as program:
            while self.running:
                try:
                    data = self.conn.recv(1024)
                    if not data:
                        break
                    lines = data.decode('utf-8', errors='ignore').split('\n')
                    for line in lines:
                        clean = line.strip()
                        if clean:
                            if clean.startswith('?') or clean.startswith('$'):
                                # Statusabfragen und Konfigurationsbefehle nur beantworten, nicht loggen
                                self.conn.sendall(b"ok\r\n")
                            else:
                                # G-Code Befehle verarbeiten
                                if not self.receiving_program:
                                    self.receiving_program = True
                                    self.program_status_callback(get_text('receiving_program'))
                                
                                program.write(clean + "\n")
                                program.flush()
                                self.conn.sendall(b"ok\r\n")
                        elif '?' in line:
                            status = b"<Idle|MPos:0.000,0.000,0.000|FS:0,0>\r\n"
                            self.conn.sendall(status)
                            # Statusaustausch wird nicht geloggt - wird durch grünes Lämpchen dargestellt
                except socket.timeout:
                    continue
                except Exception as e:
                    self.gui_callback(f"[{get_text('error')}] {e}")
                    break
        self.connected = False
        self.status_callback(get_text('connection_lost'), "yellow")
        if self.receiving_program:
            self.receiving_program = False
            self.program_status_callback(get_text('program_received'))
        try:
            self.conn.close()
        except:
            pass

    def stop(self):
        self.running = False
        self.connected = False
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass
        try:
            self.server.shutdown(socket.SHUT_RDWR)  # Socket ordnungsgemäß herunterfahren
        except:
            pass
        try:
            self.server.close()
        except:
            pass

def create_backup_file():
    """Erstellt eine Backup-Datei mit Datum und Uhrzeit"""
    if os.path.exists(PROGRAM_FILE):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"lightburn_program_{timestamp}.ngc"
        try:
            with open(PROGRAM_FILE, 'r') as source:
                with open(backup_name, 'w') as backup:
                    backup.write(source.read())
            return f"{get_text('backup_created')} {backup_name}"
        except Exception as e:
            return f"{get_text('backup_error')} {e}"
    return get_text('no_program_file')



def show_program_window():
    """Zeigt das aktuelle Programm in einem separaten Fenster"""
    if not os.path.exists(PROGRAM_FILE):
        messagebox.showwarning("Warnung", get_text('no_program_file'))
        return
    
    program_window = tk.Toplevel()
    program_window.title(get_text('current_program'))
    program_window.geometry("800x600")
    
    # Programm anzeigen
    text_area = ScrolledText(program_window, wrap=tk.WORD)
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    try:
        with open(PROGRAM_FILE, 'r') as f:
            content = f.read()
            text_area.insert(tk.END, content)
    except Exception as e:
        text_area.insert(tk.END, f"Fehler beim Lesen der Datei: {e}")
    
    text_area.config(state=tk.DISABLED)
    
    # Schließen Button
    close_button = tk.Button(program_window, text=get_text('close'), command=program_window.destroy)
    close_button.pack(pady=10)

def start_gui():
    root = tk.Tk()
    root.title(get_text('title'))

    # Status Frame
    status_frame = tk.Frame(root)
    status_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Label(status_frame, text=get_text('status')).pack(side=tk.LEFT)
    status_label = tk.Label(status_frame, text=get_text('initializing'))
    status_label.pack(side=tk.LEFT, padx=5)
    
    # Status-Lampe
    status_light = tk.Canvas(status_frame, width=20, height=20, bg="gray")
    status_light.pack(side=tk.LEFT, padx=5)
    
    # Programm Status
    program_status_label = tk.Label(status_frame, text="")
    program_status_label.pack(side=tk.RIGHT, padx=5)

    # Button Frame
    button_frame = tk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=5)
    
    backup_button = tk.Button(button_frame, text=get_text('backup_create'), 
                             command=lambda: messagebox.showinfo("Backup", create_backup_file()))
    backup_button.pack(side=tk.LEFT, padx=5)
    
    program_button = tk.Button(button_frame, text=get_text('current_program'), 
                              command=show_program_window)
    program_button.pack(side=tk.LEFT, padx=5)

    # Log Frame
    log_frame = tk.Frame(root)
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    tk.Label(log_frame, text=get_text('gcode_communication')).pack(anchor=tk.W)
    
    text_area = ScrolledText(log_frame, wrap=tk.WORD, height=25, width=100)
    text_area.pack(fill=tk.BOTH, expand=True)
    text_area.config(state=tk.DISABLED)

    def add_line(line):
        text_area.config(state=tk.NORMAL)
        if "→" in line:
            text_area.insert(tk.END, line + "\n", "sent")
        elif "←" in line:
            text_area.insert(tk.END, line + "\n", "recv")
        else:
            text_area.insert(tk.END, line + "\n")
        text_area.see(tk.END)
        text_area.config(state=tk.DISABLED)

    def update_status(message, color):
        status_label.config(text=message, fg=color)
        status_light.config(bg=color)

    def update_program_status(message):
        program_status_label.config(text=message)

    text_area.tag_config("recv", foreground="blue")
    text_area.tag_config("sent", foreground="green")

    # Server wird hier gesetzt
    def stop_gui_and_server():
        print(get_text('quitting'))
        if hasattr(root, "server"):
            root.server.stop()
        root.after(200, root.destroy)  # Längere Verzögerung für sauberes Beenden

    stop_button = tk.Button(root, text=get_text('quit'), command=stop_gui_and_server)
    stop_button.pack(pady=5)

    # Callback für sicheres GUI-Schließen
    def safe_quit():
        root.after(0, stop_gui_and_server)


    
    # TCP-Server starten
    root.server = GCodeServer(add_line, safe_quit, update_status, update_program_status)

    root.protocol("WM_DELETE_WINDOW", stop_gui_and_server)
    root.mainloop()

if __name__ == "__main__":
    start_gui()

