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
    childhood: str
    student: str
    events: str
    relationships: str
    work: str
    stress: str
    problem: str
    change: str

@app.post("/analyze")
async def analyze_life_history(request: AnalyzeRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI APIキーがサーバーに設定されていません。")

    system_prompt = f"""あなたは心理分析家・行動構造アナリストです。
ユーザーの自分史から、AI臭のない、事実に基づいた深い「人生構造分析レポート」を作成してください。

【執筆の重要ルール】
・必ずユーザーの具体的なエピソード（出来事）を引用する。
・「〜な傾向がある」「〜と言えます」といったAI特有の解説・推測を排する。
・抽象的な励まし、一般論は一切書かない。
・ユーザーの人生を一つの「ストーリー」として淡々と、かつ鋭く描写する。
・一文を短くし、行間を活かしたリズムで書く。

【出力構成（全10セクション、見出し一字一句遵守）】

## 1 人生の流れ
（ユーザーの出来事を引用しながら、人生全体のテーマを一つの物語として読み解く）

## 2 転換点
（重要度の高い出来事を3〜5個抽出。1.出来事名 2.そこでの感情と意味、を事実ベースで記述）

## 3 繰り返している構造
（人生の負のループを構造図で示す。 ↓ 記号を使用し、最後が最初に戻るループにする）

## 4 無意識の人生ルール
（出来事を根拠に、「〇〇でなければならない」等の信念を特定する）

## 5 この構造の強み
（この構造がこれまでの人生でユーザーをどう守ってきたか、メリットを記述）

## 6 この構造の代償
（この構造の維持によって、現在どのような問題や疲弊が起きているか記述）

## 7 このまま進んだ未来
（同じ構造が続いた場合、10年後どうなっているかを事実の延長から描写する）

## 8 あなたの人生構造タイプ
（以下の12タイプから1つ選定し、その理由を簡潔に：自己犠牲型, 承認追求型, 責任背負い型, 孤立防御型, 逃避型, 救世主型, コントロール型, 回避型, 献身型, 承認飢餓型, 境界崩壊型, 再起型）

## 9 構造を書き換えるヒント
（具体的な行動指針を提示）

## 10 最後
（固定テキスト：以下の文章を完全に入力すること）
この構造は
理解しただけでは止まりません。

なぜなら
これは思考ではなく
長年繰り返された反応だからです。

もし
このループを終わらせたいなら

構造解析セッションで
このパターンを整理できます。

▶ 構造解析セッションを見る

【分析データ】
幼少期: {request.childhood}
学生時代: {request.student}
出来事: {request.events}
悩み: {request.problem}
"""

    user_prompt = "10のセクション構成を厳守して分析を開始してください。AIの解説ではなく、私（ユーザー）の人生の断片をつなぎ合わせて、構造を浮き彫りにしてください。見出しは絶対に変更しないでください。"

    async with httpx.AsyncClient() as client:
        try:
            # 人生構造の解析
            response_1 = await client.post(
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
                    "temperature": 0.4,
                    "max_tokens": 3000
                },
                timeout=120.0
            )
            response_1.raise_for_status()
            result_1 = response_1.json()
            raw_content = result_1['choices'][0]['message']['content']
            
            # 見出しを強制的に置換（セクション8：人生構造タイプ）
            import re
            final_report = re.sub(r"^\s*#+\s*[8８].*", "## 8 あなたの人生構造タイプ", raw_content, flags=re.MULTILINE)

            return {"report": final_report, "raw": raw_content}
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

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.get("/")
@app.get("/analysis-form")
@app.get("/analysis-result")
@app.get("/session-lp")
async def serve_index_any():
    import os
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(index_path)

@app.get("/style.css")
async def serve_css():
    return FileResponse(os.path.join(os.path.dirname(__file__), "style.css"))

@app.get("/lp.css")
async def serve_lp_css():
    return FileResponse(os.path.join(os.path.dirname(__file__), "lp.css"))

@app.get("/script.js")
async def serve_js():
    return FileResponse(os.path.join(os.path.dirname(__file__), "script.js"))
