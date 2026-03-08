import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import whisper
import os
import sys
import shutil

# Check for local ffmpeg and add to PATH
def check_ffmpeg():
    # Check if ffmpeg is in current directory
    current_dir = os.getcwd()
    ffmpeg_path = os.path.join(current_dir, "ffmpeg.exe")
    if os.path.exists(ffmpeg_path):
         os.environ["PATH"] += os.pathsep + current_dir
         return True
    
    # Check if ffmpeg is already in PATH
    if shutil.which("ffmpeg"):
        return True
    
    return False

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Transcription Tool")
        self.root.geometry("600x500")

        # Instructions
        self.label = tk.Label(root, text="音声ファイルを選択してください (mp3, wav, m4a, etc.)", font=("Arial", 12))
        self.label.pack(pady=10)

        # File selection button
        self.select_btn = tk.Button(root, text="ファイルを選択", command=self.select_file, font=("Arial", 10), bg="#dddddd")
        self.select_btn.pack(pady=5)

        # Model selection
        self.model_frame = tk.Frame(root)
        self.model_frame.pack(pady=5)
        
        tk.Label(self.model_frame, text="モデルサイズ (精度): ", font=("Arial", 10)).pack(side=tk.LEFT)
        
        self.model_var = tk.StringVar(value="small")
        self.model_combo = ttk.Combobox(self.model_frame, textvariable=self.model_var, state="readonly", width=18)
        self.model_combo['values'] = ("base (標準)", "small (高精度)", "medium (超高精度)", "large (最高精度・重い)")
        self.model_combo.current(1) # Default to small
        self.model_combo.pack(side=tk.LEFT)
        
        tk.Label(self.model_frame, text="※初回はダウンロードが発生します", font=("Arial", 8), fg="gray").pack(side=tk.LEFT, padx=5)

        # Initial prompt (keywords)
        self.prompt_label = tk.Label(root, text="キーワード / ヒント (任意):", font=("Arial", 10))
        self.prompt_label.pack(pady=(10, 0))
        self.prompt_entry = tk.Entry(root, width=50, font=("Arial", 10))
        self.prompt_entry.pack(pady=5)
        tk.Label(root, text="専門用語や、誤変換されやすい言葉をカンマ区切りで入力してください\n例: セルフ虐待, 波風, 静かに", font=("Arial", 8), fg="gray").pack()

        # Output area
        self.output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20, font=("Arial", 10))
        self.output_area.pack(pady=10, padx=10)

        # Save button
        self.save_btn = tk.Button(root, text="テキストを保存", command=self.save_text, state=tk.DISABLED, font=("Arial", 10), bg="#dddddd")
        self.save_btn.pack(pady=5)

        self.status_label = tk.Label(root, text="", fg="blue")
        self.status_label.pack(pady=5)

        self.model = None
        self.current_model_name = None

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.mp4 *.flac"), ("All Files", "*.*")]
        )
        if file_path:
            self.output_area.delete(1.0, tk.END)
            self.status_label.config(text="モデルを読み込み中... (初回は時間がかかります)")
            
            # Get prompt text
            initial_prompt = self.prompt_entry.get()
            
            self.root.update()
            
            # Run transcription in a separate thread to keep GUI responsive
            threading.Thread(target=self.transcribe, args=(file_path, initial_prompt), daemon=True).start()

    def transcribe(self, file_path, initial_prompt=""):
        try:
            selected_model_name = self.model_var.get().split(" ")[0] # extract "base", "small", "medium"
            
            # Load model if it's not loaded or if a different model is selected
            if self.model is None or self.current_model_name != selected_model_name:
                self.update_status(f"モデル '{selected_model_name}' を読み込み中... (時間がかかります)")
                self.model = whisper.load_model(selected_model_name)
                self.current_model_name = selected_model_name
            
            self.update_status("文字起こし中... しばらくお待ちください")
            
            # Use initial_prompt to guide the model
            options = {}
            base_prompt = "会話の書き起こしです。丁寧な日本語で、句読点を正しく打ちます。慢性的、疲労、喪失、場合、いい人、性格、冷たい、代償、過剰、期待、かつて、静かに。"
            
            if initial_prompt:
                final_prompt = initial_prompt + " " + base_prompt
            else:
                final_prompt = base_prompt
                
            options["initial_prompt"] = final_prompt

            result = self.model.transcribe(file_path, **options)
            text = result["text"]

            self.root.after(0, self.show_result, text)
        except Exception as e:
            self.root.after(0, self.show_error, str(e))

    def update_status(self, message):
        self.root.after(0, lambda: self.status_label.config(text=message))

    def show_result(self, text):
        self.output_area.insert(tk.END, text)
        self.status_label.config(text="完了！")
        self.save_btn.config(state=tk.NORMAL)

    def show_error(self, message):
        self.status_label.config(text="エラーが発生しました")
        messagebox.showerror("Error", message)

    def save_text(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.output_area.get(1.0, tk.END))
            messagebox.showinfo("Saved", "ファイルを保存しました")

if __name__ == "__main__":
    try:
        import whisper
    except ImportError:
        print("Error: 'openai-whisper' library is not installed. Please run: pip install openai-whisper")
        # Creating a dummy window to show error if possible, or just exit
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependency", "ライブラリ 'openai-whisper' が見つかりません。\n'pip install openai-whisper' を実行してください。")
        sys.exit(1)

    if not check_ffmpeg():
         root = tk.Tk()
         root.withdraw()
         messagebox.showwarning("Missing FFmpeg", "FFmpegが見つかりません。\n'ffmpeg.exe' をこのアプリと同じフォルダに置いてください。")
         # We continue anyway, as whisper might find it via other means or user might install it while app is running


    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()
