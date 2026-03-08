import subprocess
import re
import sys
import time

def main():
    print("==============================================")
    print(" 準備中...数秒お待ちください。")
    print("==============================================")
    
    # Start cloudflared
    process = subprocess.Popen(
        [r".\cloudflared.exe", "tunnel", "--url", "http://127.0.0.1:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    url_found = False
    
    # Read stderr where cloudflared prints the URL
    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None:
            break
        
        # Look for the trycloudflare.com URL
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match and not url_found:
            public_url = match.group(0)
            print(f"\n 公開準備が完了しました！")
            print(f"==============================================")
            print(f" あなたの専用URL: {public_url}")
            print(f"==============================================\n")
            print("【注意】この黒い画面（コマンドプロンプトやシステム）を閉じるとURLは無効になります。")
            print("終わる時は Ctrl+C で終了してください。")
            url_found = True

        # Print underlying errors if any, but hide the noise
        if "ERR" in line or "fail" in line.lower():
            if "update" not in line.lower():
                print(f"[システムログ] {line.strip()}")

if __name__ == "__main__":
    main()
