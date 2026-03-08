from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import markdown
import pdfkit
import tempfile

load_dotenv()

app = FastAPI()

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    formattedHistory: str

@app.post("/analyze")
async def analyze_life_history(request: AnalyzeRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI APIキーがサーバーに設定されていません。")

    system_prompt = """あなたは「人生史解析AI」です。

心理診断をするのではなく、
ユーザーが入力した人生の出来事を
時系列として読み取り、

その人の人生に繰り返されている

・選択パターン 
・人間関係構造 
・環境変化 
・無意識の反応 

を分析してください。

--------------------------------

【重要ルール】

単語を説明してはいけません。

必ず

出来事 → 流れ → 構造

の順で分析してください。

--------------------------------

【分析手順】

STEP1 
人生の出来事を時系列として理解する

STEP2 
人生の転換点を特定する

・環境が大きく変わった出来事
・成功体験
・崩壊体験
・人間関係の大きな変化

STEP3 
繰り返しているパターンを抽出する

例

努力 
↓ 
成功 
↓ 
人間関係崩壊 
↓ 
環境リセット

など

STEP4 
そのパターンを「人生構造」として言語化する

--------------------------------

【文章スタイル】

AIの説明口調は禁止。

以下を守る。

・短い文章
・改行多め
・説明しすぎない
・断片的に書く
・会話のように書く
・心理カウンセラーが話すトーン

--------------------------------

【出力構造】
以下のMarkdown形式（見出しは ## を使用）で出力してください。

## 0 タイトル 
人生構造分析レポート

--------------------------------

## 1 人生の流れ

人生を時系列で整理する

--------------------------------

## 2 人生の転換点

人生の重要な分岐点を書く

--------------------------------

## 3 繰り返しているパターン

人生で何度も起きている流れを書く

--------------------------------

## 4 無意識の選択

なぜその選択をしてしまうのか

--------------------------------

## 5 強み

この構造が生む強み

--------------------------------

## 6 課題

この構造が生む問題

--------------------------------

## 7 変化のヒント

構造を変えるための行動

--------------------------------

## 8 最後のメッセージ

ここまで読んで
思い当たることがあったかもしれません。

でも
理解だけでは人生は変わりません。

なぜなら
これは思考ではなく
反応だからです。

--------------------------------

## 9 次の選択

このレポートを
気づきとして持ち帰るか。

それとも
構造を書き換えるか。

--------------------------------

## 10 次のステップ

現在
人生構造を整理する
個別解析セッションを行っています。

AIでは見えない

・本当の原因
・無意識の選択
・止める方法

まで整理します。
"""

    user_prompt = f"以下のユーザー回答を分析してください。\n\n【ユーザー回答】\n{request.formattedHistory}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        { "role": "system", "content": system_prompt },
                        { "role": "user", "content": user_prompt }
                    ],
                    "temperature": 0.0,
                    "seed": 42,
                    "max_tokens": 3000
                },
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()
            return {"report": result['choices'][0]['message']['content']}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"OpenAI APIエラー: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"通信エラー: {str(e)}")

class EmailRequest(BaseModel):
    email: str
    report_markdown: str

@app.post("/send-report")
async def send_report_email(request: EmailRequest):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    # If no SMTP server configured, simulate success (for demo)
    if not smtp_server or not smtp_user or not smtp_pass:
        print(f"[Simulation] Would have sent email to {request.email}")
        return {"status": "success", "message": "Demo mode: Email 'sent' successfully (SMTP credentials not configured)."}

    # 1. Convert Markdown to HTML
    html_content = markdown.markdown(request.report_markdown)
    
    # 追加: メールの文字化けを防ぐための <meta charset="UTF-8"> タグを追加
    # さまざまな端末で読みやすくなるようフォント指定も変更
    styled_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif; line-height: 1.6; color: #333; }}
        h2 {{ color: #333; border-bottom: 2px solid #5abcb5; padding-bottom: 5px; margin-top: 30px; }}
        h3 {{ color: #5abcb5; border-left: 3px solid #5abcb5; padding-left: 10px; margin-top: 20px; }}
        h4 {{ color: #444; }}
        .report-container {{ padding: 20px; max-width: 800px; margin: 0 auto; }}
        p {{ margin-bottom: 1em; }}
    </style>
    </head>
    <body>
    <div class="report-container">
        <h2>わたしの人生パターンレポート</h2>
        {html_content}
    </div>
    </body>
    </html>
    """

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication

    try:
        # EmailMessageオブジェクトを作成
        msg = EmailMessage()
        msg['Subject'] = '【人生パターン・レポート】解析結果をお届けします'
        if smtp_user:
            msg['From'] = smtp_user
        msg['To'] = request.email
        
        # プレーンテキスト（HTMLが表示できないメールソフト用）
        body_text = "あなたの人生パターンレポートが完成しました。\n\n"
        body_text += "本メールはHTML形式で送信されています。お使いのメールソフトで表示を有効にしてご覧ください。\n\n"
        body_text += "※このメールは自動送信されています。"
        
        # 1. まずテキスト本文をセット（文字化けを防ぐためutf-8指定）
        msg.set_content(body_text, charset='utf-8')
        
        # 2. HTML版も追加（これにより「HTMLメール」として認識される）
        msg.add_alternative(styled_html, subtype='html', charset='utf-8')

        # メールサーバ経由で送信（長時間のフリーズを防ぐためタイムアウトを10秒に設定）
        with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            
        return {"status": "success", "message": "Email sent successfully"}
    except Exception as e:
        print(f"Email error: {e}")
        raise HTTPException(status_code=500, detail=f"メール送信エラー: {str(e)}")

# Run with: uvicorn main:app --reload

from fastapi.responses import FileResponse

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

@app.get("/analysis-form")
async def serve_form():
    return FileResponse("index.html")

@app.get("/analysis-result")
async def serve_result():
    return FileResponse("index.html")

@app.get("/debug-key")
async def debug_key():
    api_key = os.getenv("OPENAI_API_KEY", "")
    if len(api_key) > 4:
        return {"key_ends_with": api_key[-4:]}
    return {"key_ends_with": "too short or empty"}

@app.get("/style.css")
async def serve_css():
    return FileResponse("style.css")

@app.get("/lp.css")
async def serve_lp_css():
    return FileResponse("lp.css")

@app.get("/script.js")
async def serve_js():
    return FileResponse("script.js")
