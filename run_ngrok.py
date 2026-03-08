import os
import sys
import time
import subprocess
from pyngrok import ngrok

def main():
    print("NGROKトンネルを起動しています...")
    # Open a ngrok tunnel to the dev server
    public_url = ngrok.connect(8000).public_url
    print(f"\n==============================================")
    print(f"🌟 あなた専用の公開URLが生成されました！ 🌟")
    print(f"👉 {public_url}")
    print(f"==============================================\n")
    print("この画面（黒い画面）を開いたままにしておけば、24時間アクセス可能です。")
    print("終了するには Ctrl+C を押してください。")
    
    try:
        # Keep the process alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("NGROKトンネルを終了しました。")

if __name__ == '__main__':
    main()
