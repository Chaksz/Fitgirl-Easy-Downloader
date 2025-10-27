import os
import re
import requests
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from bs4 import BeautifulSoup
from datetime import datetime
import time

# --- Kelas Inti Aplikasi GUI ---

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minimalist Downloader")
        self.root.geometry("800x600")

        # --- Variabel Status ---
        self.download_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "Downloads"))
        self.links_changed = tk.BooleanVar(value=False)
        self.is_running = False
        self.should_stop = False 
        self.should_skip = False 
        self.progress_text_var = tk.StringVar(value="0.00%") # Untuk persentase
        self.speed_text_var = tk.StringVar(value="Speed: N/A") # Untuk kecepatan

        # --- Konfigurasi Tema Dark Mode ---
        self.colors = {
            'bg': '#000000',
            'fg': '#D3D3D3',
            'input_bg': '#141414',
            'button': '#353535',
            'button_fg': '#FFFFFF',
            'accent': '#007ACC',
            'success': '#4CAF50',
            'progress': '#4CAF50' ,
            'error': '#F44336',
            'info': '#2196F3',
            'warning': '#FFC107',
            'done': '#9C27B0',
            'stop': '#F44336',
            'skip': '#FFC107'
        }
        
        self.root.configure(bg=self.colors['bg'])
        self.setup_style()
        self.create_widgets()

        # --- Inisialisasi Logger GUI ---
        self.log = GuiConsole(self.log_text, self.root, self.colors)
        
        # Buat folder download default jika belum ada
        os.makedirs(self.download_path_var.get(), exist_ok=True)
        
        # Muat link dari input.txt saat startup
        self.load_links_from_file()
        
        # Pantau perubahan pada kotak teks link
        self.link_text.bind("<KeyRelease>", self.on_links_changed)

    def setup_style(self):
        """Mengkonfigurasi style ttk untuk dark mode."""
        style = ttk.Style()
        style.theme_use('clam') 

        # Style umum
        style.configure('.',
                        background=self.colors['bg'],
                        foreground=self.colors['fg'],
                        fieldbackground=self.colors['input_bg'],
                        bordercolor=self.colors['bg'],
                        lightcolor=self.colors['bg'],
                        darkcolor=self.colors['bg'])

        # Style Tombol
        style.configure('TButton',
                        background=self.colors['button'],
                        foreground=self.colors['button_fg'],
                        font=('Helvetica', 10),
                        padding=5)
        style.map('TButton',
                  background=[('active', self.colors['accent']),
                              ('disabled', '#555555')],
                  foreground=[('disabled', '#999999')])
                  
        # Style Tombol Baru untuk Stop/Skip
        style.configure('Stop.TButton', background=self.colors['stop'], foreground=self.colors['button_fg'])
        style.map('Stop.TButton',
                  background=[('active', '#D32F2F'), ('disabled', '#555555')])
                  
        style.configure('Skip.TButton', background=self.colors['skip'], foreground=self.colors['bg'])
        style.map('Skip.TButton',
                  background=[('active', '#FFA000'), ('disabled', '#555555')],
                  foreground=[('disabled', '#999999')])

        # Style Entry (untuk path)
        style.configure('TEntry',
                        fieldbackground=self.colors['input_bg'],
                        foreground=self.colors['fg'],
                        insertcolor=self.colors['fg'])
        style.map('TEntry',
                  fieldbackground=[('disabled', self.colors['input_bg'])],
                  foreground=[('disabled', self.colors['fg'])])

        # Style Progressbar
        style.configure('Horizontal.TProgressbar',
                        troughcolor=self.colors['input_bg'],
                        background=self.colors['progress'],
                        bordercolor=self.colors['input_bg'])
        
        # Style Label
        style.configure('TLabel', font=('Helvetica', 10))


    def create_widgets(self):
        """Membuat dan menata semua widget di jendela."""
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill='both', expand=True)

        # --- 1. Frame Path Download ---
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill='x', pady=5)

        ttk.Label(path_frame, text="Download Folder:").pack(side='left', padx=(0, 5))
        
        self.path_entry = ttk.Entry(path_frame, textvariable=self.download_path_var, state='disabled')
        self.path_entry.pack(side='left', fill='x', expand=True)

        self.browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_folder)
        self.browse_button.pack(side='left', padx=(5, 0))

        # --- 2. Frame Input Link ---
        links_frame = ttk.Frame(main_frame)
        links_frame.pack(fill='x', pady=5)

        ttk.Label(links_frame, text="Input Links:").pack(anchor='w')
        
        # Frame untuk Text Box dan Save Button
        text_button_frame = ttk.Frame(links_frame)
        text_button_frame.pack(fill='both', expand=True)

        self.link_text = scrolledtext.ScrolledText(text_button_frame,
                                                 height=10,
                                                 wrap=tk.WORD,
                                                 bg=self.colors['input_bg'],
                                                 fg=self.colors['fg'],
                                                 insertbackground=self.colors['fg'],
                                                 font=('Consolas', 10),
                                                 border=0,
                                                 relief='solid')
        self.link_text.pack(side='left', fill='both', expand=True)

        self.save_button = ttk.Button(text_button_frame, text="Save", command=self.save_links, state='disabled')
        self.save_button.pack(side='right', anchor='n', padx=(10, 0))

        # --- 3. Tombol Kontrol ---
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=10)

        # Tombol Start/Stop/Skip
        self.start_button = ttk.Button(control_frame, text="Start Downloads", command=self.start_download_thread)
        self.start_button.pack(side='left', fill='x', expand=True)
        
        self.skip_button = ttk.Button(control_frame, text="Skip Current", command=self.skip_current_download, style='Skip.TButton', state='disabled')
        self.skip_button.pack(side='left', fill='x', expand=True, padx=(10, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop All", command=self.stop_all_downloads, style='Stop.TButton', state='disabled')
        self.stop_button.pack(side='left', fill='x', expand=True)

        # --- 4. Progress Bar & Info ---
        progress_info_frame = ttk.Frame(main_frame)
        progress_info_frame.pack(fill='x', pady=(5, 0))

        self.progress_bar = ttk.Progressbar(progress_info_frame, orient='horizontal', mode='determinate', length=100)
        self.progress_bar.pack(side='left', fill='x', expand=True, padx=(0, 10))

        # Label Persentase
        self.percent_label = ttk.Label(progress_info_frame, textvariable=self.progress_text_var, width=6)
        self.percent_label.pack(side='right')

        # Label Kecepatan
        self.speed_label = ttk.Label(progress_info_frame, textvariable=self.speed_text_var, width=15)
        self.speed_label.pack(side='right', padx=(10, 0))


        # --- 5. Status Log ---
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill='both', expand=True, pady=(10, 5))

        ttk.Label(log_frame, text="Status Log:").pack(anchor='w')
        
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 wrap=tk.WORD,
                                                 state='disabled',
                                                 bg=self.colors['input_bg'],
                                                 fg=self.colors['fg'],
                                                 font=('Consolas', 9),
                                                 border=0,
                                                 relief='solid')
        self.log_text.pack(fill='both', expand=True)

    # --- Fungsi Callback Widget ---

    def browse_folder(self):
        """Membuka dialog untuk memilih folder download."""
        folder = filedialog.askdirectory(initialdir=self.download_path_var.get())
        if folder:
            self.download_path_var.set(folder)
            os.makedirs(folder, exist_ok=True)
            self.log.info("Download folder set to", folder)

    def load_links_from_file(self):
        """Membaca input.txt dan mengisinya ke text box."""
        try:
            if os.path.exists('input.txt'):
                with open('input.txt', 'r') as f:
                    links = f.read()
                    self.link_text.insert('1.0', links)
                self.log.info("Loaded links from", 'input.txt')
            else:
                self.log.info("input.txt not found.", "Creating a new one on save.")
            self.save_button.config(state='disabled')
            self.links_changed.set(False)
        except Exception as e:
            self.log.error("Failed to read input.txt", str(e))

    def on_links_changed(self, event=None):
        """Dipanggil setiap kali teks di kotak link berubah."""
        if not self.is_running:
            self.save_button.config(state='normal')
            self.links_changed.set(True)

    def save_links(self):
        """Menyimpan konten text box ke input.txt."""
        try:
            links = self.link_text.get('1.0', 'end-1c') 
            with open('input.txt', 'w') as f:
                f.write(links)
            self.log.done("Links saved to", 'input.txt')
            self.save_button.config(state='disabled')
            self.links_changed.set(False)
        except Exception as e:
            self.log.error("Failed to save input.txt", str(e))

    def skip_current_download(self):
        """Mengatur flag untuk melewati download saat ini."""
        if self.is_running:
            self.should_skip = True
            self.log.warning("Skip requested.", "Moving to next link...")
            self.skip_button.config(state='disabled') 

    def stop_all_downloads(self):
        """Mengatur flag untuk menghentikan semua proses download."""
        if self.is_running:
            self.should_stop = True
            self.log.error("Stop requested.", "Stopping all downloads...")
            self.stop_button.config(state='disabled')
    
    def set_controls_state(self, state):
        """Mengaktifkan/menonaktifkan tombol selama proses download."""
        self.start_button.config(state=state)
        self.browse_button.config(state=state)
        
        # Mengelola tombol Stop/Skip
        if state == 'disabled':
            self.is_running = True
            self.should_stop = False # Reset flag stop saat start
            self.should_skip = False # Reset flag skip saat start
            self.stop_button.config(state='normal')
            self.skip_button.config(state='normal')
            self.save_button.config(state='disabled')
        else:
            self.is_running = False
            self.stop_button.config(state='disabled')
            self.skip_button.config(state='disabled')
            if self.links_changed.get():
                self.save_button.config(state='normal')

    # >> FUNGSI BARU: Menghapus Link dari GUI dan File <<
    def remove_link_from_gui_and_file(self, processed_link):
        """Menghapus tautan yang berhasil diunduh dari GUI dan input.txt.
           Ini dipanggil dari thread download, sehingga pemrosesan file aman.
           Pembaruan GUI dijadwalkan ke main thread.
        """
        input_file = 'input.txt'
        try:
            # 1. Update input.txt (Dilakukan di thread kerja)
            with open(input_file, 'r') as file:
                links = file.readlines()
                
            # Filter tautan yang berhasil diunduh
            remaining_links = [line for line in links if line.strip() != processed_link.strip()]
            
            with open(input_file, 'w') as file:
                file.writelines(remaining_links)
                
            # Hitung tautan non-kosong yang tersisa
            remaining_count = len([link for link in remaining_links if link.strip()])

            self.log.done("Link Removed From input.txt", f"Remaining links: {remaining_count}")
            
            # 2. Update GUI Text Box (Dijadwalkan di main thread)
            def update_gui_text():
                self.link_text.config(state='normal')
                self.link_text.delete('1.0', 'end')
                # Masukkan kembali tautan yang tersisa
                self.link_text.insert('1.0', "".join(remaining_links))
                self.link_text.config(state='normal') 
                self.on_links_changed() # Reset status save button
                
            self.root.after(0, update_gui_text)

        except Exception as e:
            self.log.error(f"Failed to remove link {processed_link} from file/GUI", str(e))
    # ----------------------------------------------------

    # --- Logika Download (di-thread) ---

    def start_download_thread(self):
        """Memulai proses download di thread baru."""
        self.set_controls_state('disabled')
        self.log.info("Starting download process...", "")
        # Reset display
        self.root.after(0, self.update_progress, 0, "N/A", "N/A")
        # Buat thread baru
        download_thread = threading.Thread(target=self.run_download_loop, daemon=True)
        download_thread.start()

    def run_download_loop(self,):
        """Loop utama yang memproses setiap link. (Berjalan di thread)"""
        
        # Ambil link dari text box (Ini adalah daftar statis untuk sesi ini)
        links_raw = self.link_text.get('1.0', 'end-1c')
        links = [line.strip() for line in links_raw.splitlines() if line.strip()]

        if not links:
            self.log.warning("No links to process.", "")
            self.root.after(0, self.set_controls_state, 'normal')
            return

        # Headers dari skrip asli
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.5',
            'referer': 'https://fitgirl-repacks.site/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        
        downloads_folder = self.download_path_var.get()
        
        # --- di run_download_loop (ganti bagian for link in links) ---
        for link in links:
            # Cek status Stop
            if self.should_stop:
                self.log.error("Global stop received.", "Stopping link processing.")
                break

            # Kalau skip ditekan, jangan reset di sini!
            if self.should_skip:
                self.log.warning("Skipping link", link)
                continue  # lanjut ke link berikutnya
            
            self.root.after(0, self.skip_button.config, {'state': 'normal'}) 
            self.log.info("Processing", link)
            self.root.after(0, self.update_progress, 0, "0.00%", "Speed: N/A")

            try:
                response = requests.get(link, headers=headers, timeout=10)
                if response.status_code != 200:
                    self.log.error("Failed to fetch page", f"{link} (Status: {response.status_code})")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                meta_title = soup.find('meta', attrs={'name': 'title'})
                file_name_raw = meta_title['content'] if meta_title else "default_file_name"
                file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name_raw)

                script_tags = soup.find_all('script')
                download_function = None
                for script in script_tags:
                    if 'function download' in script.text:
                        download_function = script.text
                        break

                if download_function:
                    match = re.search(r'window\.open\(["\'](https?://[^\s"\'\)]+)', download_function)
                    if match:
                        download_url = match.group(1)
                        self.log.info("Found URL", f"{download_url[:50]}...")
                        output_path = os.path.join(downloads_folder, file_name)
                        self.download_file(download_url, output_path, file_name_raw, link)
                    else:
                        self.log.error("No download URL found", link)
                else:
                    self.log.error("Download function not found", link)

            except Exception as e:
                self.log.error(f"Failed processing link {link}", str(e))
                continue

        # Penanganan Akhir Loop Download
        if self.should_stop:
            self.log.done("Download process cancelled by user.", "")
        else:
            self.log.done("All download tasks finished.", "")
            
        self.root.after(0, self.update_progress, 0, "0.00%", "Speed: N/A") # Reset tampilan progress
        self.root.after(0, self.set_controls_state, 'normal') # Aktifkan kembali tombol

    # >> FUNGSI DOWNLOAD DIMODIFIKASI untuk memanggil penghapusan link <<
    def download_file(self, download_url, output_path, file_name_raw, link_to_remove):
        """Mendownload file, memperbarui progress bar, dan menghapus link jika sukses."""
        try:
            start_time = time.time()
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            total_size_human = self.format_size(total_size)
            self.log.info(f"Downloading {file_name_raw} ({total_size_human})", f"{download_url[:0]}...")

            block_size = 8192
            downloaded_size = 0
            last_time = start_time
            last_downloaded = 0

            with open(output_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    # Cek Status Stop/Skip
                    if self.should_stop or self.should_skip: 
                        raise StopIteration("Download cancelled.") 

                    f.write(data)
                    downloaded_size += len(data)
                    
                    current_time = time.time()
                    
                    if current_time - last_time >= 0.5: # Update speed setiap 0.5 detik
                        delta_t = current_time - last_time
                        delta_bytes = downloaded_size - last_downloaded
                        
                        speed_bps = delta_bytes / delta_t
                        speed_human = self.format_speed(speed_bps)
                        
                        progress = (downloaded_size / total_size) * 100 if total_size > 0 else 0
                        percent_human = f"{progress:.2f}%"
                        
                        # Jadwalkan update UI di main thread
                        self.root.after(0, self.update_progress, progress, percent_human, f"Speed: {speed_human}")
                        
                        last_time = current_time
                        last_downloaded = downloaded_size
            
            # JIKA SUKSES: Panggil fungsi penghapusan link
            self.remove_link_from_gui_and_file(link_to_remove)
            
            # Final logging
            end_time = time.time()
            total_duration = end_time - start_time
            avg_speed_bps = downloaded_size / total_duration if total_duration > 0 else 0
            avg_speed_human = self.format_speed(avg_speed_bps)
            
            self.log.success(f"Downloaded in {total_duration:.2f}s (Avg. {avg_speed_human})", f"{output_path}")
            self.root.after(0, self.update_progress, 100, "100.00%", f"Done! ({avg_speed_human})")
            
        except requests.exceptions.RequestException as e:
            self.log.error(f"Download failed for {file_name_raw}", str(e))
            self.root.after(0, self.update_progress, 0, "0.00%", "Speed: N/A")
            if os.path.exists(output_path):
                 try:
                    os.remove(output_path)
                    self.log.info("Removed partial file", output_path)
                 except Exception:
                    self.log.warning("Could not remove partial file", output_path)
        except StopIteration:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    self.log.info("Removed partial file", output_path)
                except Exception:
                    self.log.warning("Could not remove partial file", output_path)
            
            if self.should_stop:
                self.log.error("Download stopped by user.", f"Cancelled: {file_name_raw}")
            elif self.should_skip:
                self.log.warning("Download skipped by user.", f"Skipped: {file_name_raw}. Moving to next link...")
                self.should_skip = False  # reset di sini, bukan di run_download_loop

        except Exception as e:
            self.log.error(f"Error writing file {file_name_raw}", str(e))
            self.root.after(0, self.update_progress, 0, "0.00%", "Speed: N/A")
    # --------------------------------------------------------------------------

    # --- Fungsi Utilitas ---
    
    def format_size(self, size_bytes):
        """Mengkonversi bytes menjadi string yang mudah dibaca (KB, MB, GB)."""
        if size_bytes == 0:
            return "0B"
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1
        return f"{size_bytes:.2f}{units[i]}"

    def format_speed(self, speed_bps):
        """Mengkonversi bytes/second menjadi string yang mudah dibaca (KB/s, MB/s)."""
        return self.format_size(speed_bps).replace('B', 'B/s')
        
    def update_progress(self, value, percent_str, speed_str):
        """Memperbarui nilai progress bar, persentase, dan kecepatan. (Dipanggil via root.after)"""
        self.progress_bar['value'] = value
        self.progress_text_var.set(percent_str)
        self.speed_text_var.set(speed_str)


# --- Kelas Logger GUI (Pengganti 'console') ---
class GuiConsole:
    """Kelas untuk logging ke widget Teks Tkinter secara thread-safe."""
    def __init__(self, log_widget, root, colors):
        self.log_widget = log_widget
        self.root = root
        
        # Tentukan tag warna di widget Teks
        self.log_widget.tag_config('TIMESTAMP', foreground='#AAAAAA')
        self.log_widget.tag_config('SUCCESS', foreground=colors['success'])
        self.log_widget.tag_config('ERROR', foreground=colors['error'])
        self.log_widget.tag_config('DONE', foreground=colors['done'])
        self.log_widget.tag_config('WARNING', foreground=colors['warning'])
        self.log_widget.tag_config('INFO', foreground=colors['info'])
        self.log_widget.tag_config('MSG', foreground=colors['fg'])

    def _write_log(self, parts):
        """Fungsi internal untuk menulis ke log. HARUS dijalankan di main thread."""
        self.log_widget.config(state='normal')
        
        self.log_widget.insert('end', parts[0][0], parts[0][1]) # Timestamp
        self.log_widget.insert('end', parts[1][0], parts[1][1]) # Tipe log
        self.log_widget.insert('end', parts[2][0], parts[2][1]) # Pesan
        self.log_widget.insert('end', parts[3][0], parts[3][1]) # Objek
        self.log_widget.insert('end', '\n')
        
        self.log_widget.see('end') # Auto-scroll
        self.log_widget.config(state='disabled')

    def _log(self, tag, message, obj):
        """Memformat pesan dan menjadwalkannya untuk ditulis di main thread."""
        timestamp = f"{datetime.now().strftime('%H:%M:%S')} » "
        tag_str = f"{tag.upper():<5} • "
        msg_str = f"{message} : "
        obj_str = f"{obj}"
        
        # Buat daftar tuple (teks, tag)
        parts = [
            (timestamp, 'TIMESTAMP'),
            (tag_str, tag.upper()),
            (msg_str, 'MSG'),
            (obj_str, tag.upper())
        ]
        
        # Jadwalkan penulisan log di main thread
        self.root.after(0, self._write_log, parts)

    # --- Metode logging publik ---
    def success(self, message, obj):
        self._log('success', message, obj)

    def error(self, message, obj):
        self._log('error', message, obj)

    def done(self, message, obj):
        self._log('done', message, obj)

    def warning(self, message, obj):
        self._log('warning', message, obj)

    def info(self, message, obj):
        self._log('info', message, obj)


# --- Titik Masuk Program ---

if __name__ == "__main__":
    main_root = tk.Tk()
    app = DownloaderApp(main_root)
    main_root.mainloop()
