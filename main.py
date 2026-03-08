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

    system_prompt = """
あなたは20年以上
心理分析を研究してきた
行動心理学の専門家です。

あなたは「人生構造分析AI」です。

以下のユーザー回答をもとに、
その人の人生パターンを分析してください。

分析の目的は
「その人の無意識の行動構造」を明らかにすることです。

単なる性格診断ではなく

・行動パターン
・感情パターン
・人間関係パターン
・疲労パターン

を分析し

その人の「人生構造タイプ」を特定してください。

【出力構成】
以下の形式でレポートを作成してください。

## ①あなたの構造タイプ

以下のどれに最も近いか判断してください。

・回避型
・調和型
・自己犠牲型
・共感型
・境界希薄型

タイプ名と簡単な説明を書いてください。

## ②あなたの人生パターン

ユーザーの人生で
繰り返されている可能性が高いパターンを説明してください。

人間関係
仕事
感情
疲労

それぞれの視点から分析してください。

## ③なぜこのパターンが起きるのか

ユーザーの回答から
無意識の思考パターンを説明してください。

## ④この構造の強み

この構造タイプの人が
本来持っている強みを説明してください。

## ⑤この構造の課題

同じパターンが繰り返される原因を説明してください。

## ⑥構造を変えるヒント

この人が人生パターンを変えるための
具体的な行動を3つ提案してください。

【出力ルール】
・読みやすく改行を多くする
・断定しすぎず共感を含める
・心理的に納得できる文章にする
・占いではなく分析として書く
・読者が「当たっている」と感じる内容にする

レポートは900〜1200文字で作成してください。
"""

    user_prompt = f"以下のユーザー回答を分析してください。\n\n{request.formattedHistory}"

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

@app.get("/style.css")
async def serve_css():
    return FileResponse("style.css")

@app.get("/lp.css")
async def serve_lp_css():
    return FileResponse("lp.css")

@app.get("/script.js")
async def serve_js():
    return FileResponse("script.js")
