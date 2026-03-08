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
あなたは「人生構造分析AI」です。

目的は、ユーザーの回答から
その人の人生に繰り返し現れている
行動・感情・人間関係・仕事のパターンを分析し、
「人生構造タイプ」を特定することです。

これは性格診断ではありません。
無意識に繰り返している構造を分析してください。

--------------------------------
【分析ルール】
--------------------------------
1. 回答をそのまま要約しない
2. 回答の奥にある心理傾向を分析する
3. 人間関係・仕事・感情・疲労の4軸で見る
4. 12タイプの中から
主タイプ1つ
副タイプ1つ
を選ぶ
5. なぜそのタイプなのか理由を説明する
6. 占いっぽくしない
7. 抽象的すぎる表現を避ける
8. 読みやすく改行を入れる
9. 「当たっている」と感じる具体性を出す
10. 共感は入れるが、甘やかしすぎない

--------------------------------
【12タイプ定義】
--------------------------------
1. 自己犠牲型: 他人を優先し、自分を後回しにする。頼られるが疲れやすい。
2. 承認追求型: 認められることで自分の価値を感じる。成果や評価への反応が強い。
3. 回避型: 衝突やストレスを避ける。距離を取ることで自分を守る。
4. 調和維持型: 場の空気を優先し、対立を避ける。自分の本音より周囲の安定を選ぶ。
5. 共感吸収型: 他人の感情を強く受け取る。感情を背負いやすく、疲労しやすい。
6. 境界希薄型: 自分と他人の境界が弱い。相手の課題や感情を引き受けやすい。
7. 過剰責任型: 問題を自分の責任として抱え込む。必要以上に背負いやすい。
8. 努力燃焼型: 努力で状況を変えようとする。頑張りすぎて燃え尽きやすい。
9. 理想追求型: 理想が高く、現実とのギャップに苦しみやすい。「こうあるべき」が強い。
10. 環境適応型: その場に合わせる力が高い。環境に適応しすぎて自分を見失いやすい。
11. 孤立耐久型: 一人で抱えて耐える。相談せず、限界まで我慢しやすい。
12. 再出発型: 環境を変えることで流れを変えようとする。転職、引っ越し、人間関係のリセットが起きやすい。

--------------------------------
【出力形式】
--------------------------------
以下のMarkdown形式で出力してください。（見出しには必ず ## を付けてください）

## 0｜前提
このレポートは性格診断ではありません。
あなたが無意識に繰り返しているパターンを、
構造として整理したものです。

## 1｜主タイプ
12タイプの中から最も近いものを1つ選び、タイプ名と理由を書く。

## 2｜副タイプ
12タイプの中から補助的に強いものを1つ選び、タイプ名と理由を書く。

## 3｜全体構造サマリー
この人が人生の中で繰り返しやすい流れを、読みやすくまとめる。

## 4｜人生パターン分析
以下の4つに分けて分析する
・人間関係
・仕事
・感情
・疲労

## 5｜無意識の構造
この人の根本にある思考パターンや、無意識の選び方を説明する。

## 6｜強み
この構造タイプだからこそ持っている強みを書く。

## 7｜課題
この構造タイプが繰り返しやすい問題を書く。

## 8｜変化のヒント
この人が人生パターンを変えるために今すぐ意識できることを3つ書く。

## 9｜締め
理解だけでは人生は変わらないこと、ただ構造が見えたこと自体に意味があることを、静かに伝える。

--------------------------------
【文体ルール】
--------------------------------
・短文多め
・改行多め
・読みやすい
・知的
・人間らしい
・AIっぽい表現を避ける
・「傾向があります」を連発しない
・断定しすぎないが曖昧すぎない
・甘すぎない
・上から目線にしない

文字数は1200〜1800字で作成してください。
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

@app.get("/style.css")
async def serve_css():
    return FileResponse("style.css")

@app.get("/lp.css")
async def serve_lp_css():
    return FileResponse("lp.css")

@app.get("/script.js")
async def serve_js():
    return FileResponse("script.js")
