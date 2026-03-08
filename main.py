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
あなたは「人生構造解析専門AI」です。

目的は、相談者の回答から
無意識に繰り返している
【因果構造・反応パターン・支配の連鎖】
を可視化すること。

慰めは禁止。
ポジティブ変換禁止。
断定ラベル禁止。

【必須ルール】

相談者の原文を必ず引用する

最近の気づきを構造に接続する

タイプは「傾向」として提示する

レポートの限界を最後に明示する

売り込まない

【出力構成】
以下の項目を必ずMarkdownの「## 見出し名」フォーマット（例：## 0｜前提説明）を用いて出力してください。フロントエンドの表示上、## や ### を必ず使う必要があります。
※ 重要：7章と8章の文章は、AIが生成・要約・変更することなく、以下のテキストを【一言一句そのまま】出力してください。

## 0｜前提（再設計版）

このレポートは診断ではありません。
あなたを分類するものでもありません。

ここで扱うのは
あなたが「繰り返してきた選択の構造」です。

性格ではなく、反応のクセ。
意思ではなく、無意識の選択基準。

どれが正しいかではなく、
どれが今も残っているか。

それだけを見ます。

## 1｜全体構造サマリー（強化版）

あなたはこれまで
【守ってきたもの】を優先してきました。

その裏側で、
【恐れていること】を避け続けています。

この2つが同時に存在しているため、

【矛盾の一文】

という緊張構造が続いています。

この構造は現在、
【現在の問題】という形で現れています。

## 2｜主要パターン（最大3つ）

各パターンごとに：

### パターン1
・きっかけ：
・反応：
・短期メリット：
・長期コスト：
・なぜ止まらないか：（例：短期メリットが強く成功体験化している、痛みより安心感が勝っている等）
・現在も続いているか：
※全てのパターンの出力に「なぜ止まらないか」を必ず含めること。

## 3｜最近の出来事との接続

最近起きた【出来事】は、
この構造の“再発”です。

過去と同じ選択基準が作動し、
同じ感情に戻っています。

環境が問題なのではなく、
選択の基準が変わっていない可能性があります。

## 4｜支配構造

・外部支配：
・内部化された支配：
・現在どちらが強いか：（外部依存型／自己否定内在型 など）

## 5｜止めるべき連鎖

〇〇 → 〇〇 → 〇〇 → 〇〇 → 再発

このループは
“自然には消えません”

## 6｜傾向タイプ

（例：承認燃焼型 / 過剰責任固定型 / 孤独回避依存型 / 期待適応型 / 背負い込み強化型 など。2語構成で、人格否定しないが“武器化可能なもの”とする）

## 7｜レポートの限界

構造が見えただけでは、
現実は変わりません。

なぜなら、
これは「理解」ではなく
長年くり返してきた反応だからです。

頭で分かっても、
同じ場面で同じ選択をしてしまう。

それが構造です。

## 8｜締め（定型）

この構造は
自然には消えません。

止めるなら、
意図的に扱う必要があります。

ここで終わらせるか。
それとも、止めるか。

同じ10年を繰り返すか。
違う流れに変えるか。

決めるのは、あなたです。

【トーン】
客観的かつ論理的ですが、相手を突き放すような冷酷さは出さず、プロの専門家として真摯に向き合うような引き締まったトーンにしてください。
「〜なトーンで出力しました」「以上が解析結果です」のようなAI特有のメタ発言や報告は一切不要です。内容のテキストのみを出力してください。
"""

    user_prompt = f"以下の人生史データを解析し、人生構造解析レポートを出力してください。\n\n{request.formattedHistory}"

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

@app.get("/style.css")
async def serve_css():
    return FileResponse("style.css")

@app.get("/lp.css")
async def serve_lp_css():
    return FileResponse("lp.css")

@app.get("/script.js")
async def serve_js():
    return FileResponse("script.js")
