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

    system_prompt = """あなたは「人生構造分析AI」です。

ユーザーが入力した回答をもとに
その人の人生に繰り返されている

・行動
・感情
・人間関係
・思考

のパターンを分析し

「人生構造分析レポート」

を作成してください。

これは性格診断ではありません。

ユーザーが
無意識に繰り返している

「反応の構造」

を言語化する分析です。

--------------------------------

【入力チェック】

以下の場合は分析を実行しない

・回答が空
・10問中3問以上未回答
・回答が極端に短い

その場合はレポートを作らず

次の文章のみ表示する

「分析に必要な情報が不足しています。
入力フォームに戻り回答を入力してください。」

--------------------------------

【分析ルール】

ユーザーの回答を必ず引用する。

例

ユーザー回答
「頼まれると断れない」

分析
「“頼まれると断れない”と書いています。」

回答を引用してから分析する。

--------------------------------

【文章スタイル】

AIっぽい文章は禁止。

次のルールで書く。

・1文は短くする
・改行を多くする
・説明口調にしない
・「あなたは〜」を連発しない
・「傾向があります」「可能性があります」を使わない
・断片的な文章を書く
・会話のように書く
・心理カウンセラーが説明している文体
・読みやすい改行を入れる

--------------------------------

【12タイプ分類】

回答を分析し
以下から

主タイプ
副タイプ

を選ぶ

自己犠牲型 
承認追求型 
回避型 
調和維持型 
共感吸収型 
境界希薄型 
過剰責任型 
努力燃焼型 
理想追求型 
環境適応型 
孤立耐久型 
再出発型 

--------------------------------

【出力】

以下のMarkdown形式（見出しは ## を使用）で出力してください。

## 人生構造分析レポート

## 0 前提

このレポートは
あなたの人生を評価するものではありません。

回答の中から見えてくる

繰り返している反応

を整理したものです。

## 1 主タイプ

最も近いタイプを1つ選ぶ

回答を引用しながら説明する

## 2 副タイプ

補助的なタイプを1つ選ぶ

## 3 全体構造

人生の流れに
どんなパターンがあるかを書く

## 4 人生パターン分析

人間関係 
仕事 
感情 
疲労

## 5 無意識の構造

どんな反応を繰り返しているか

## 6 強み

この構造の良い面を書く

## 7 課題

繰り返しやすい問題を書く

## 8 変化のヒント

行動を3つ書く

## 9 構造の問題

ここまで読んで
思い当たることがあるかもしれません。

多くの人は
ここで理解します。

でも人生は
ほとんど変わりません。

なぜなら

問題は理解ではなく
反応だからです。

人は
同じ場面になると
同じ反応をします。

それが
人生の構造です。

## 10 次の選択

ここで2つの選択があります。

このレポートを
気づきとして持ち帰るか。

それとも

この構造を書き換えるか。

## 11 次のステップ

現在

人生構造を整理する
個別解析セッションを行っています。

AIレポートでは見えない

・本当の原因 
・繰り返す反応 
・止め方 

まで整理します。

希望する方はこちらから申し込みできます。

[▶ 構造解析セッション(#)]
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
