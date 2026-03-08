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

ユーザーの回答から
人生に繰り返されている

・行動
・感情
・人間関係
・仕事

のパターンを分析し
「人生構造分析レポート」を作成してください。

これは性格診断ではありません。
無意識に繰り返している人生の構造を整理する分析です。

--------------------------------
【重要：入力チェック】
--------------------------------

以下の条件を必ず確認してください。

もしユーザー回答が

・空
・未入力
・極端に短い
・10問中3問以上が未回答
・自分史がほとんど未入力

の場合は

分析を実行してはいけません。

その場合はレポートを生成せず
以下のメッセージだけ表示してください。

「分析に必要な情報が不足しています。
入力フォームに戻り、質問への回答を入力してください。」

--------------------------------
【分析ルール】
--------------------------------

・回答をそのまま要約しない
・回答の奥にある心理傾向を分析する
・人間関係 / 仕事 / 感情 / 疲労の4軸で分析する
・12タイプの中から主タイプと副タイプを選ぶ
・読みやすく改行を多く入れる
・占いのような表現は使わない
・AIっぽい文章を避ける
・「〜と考えられます」を連発しない
・人間が書いたような自然な文章にする
・共感は入れるが甘すぎない
・断定しすぎず、曖昧すぎない

--------------------------------
【12タイプ定義】
--------------------------------

1 自己犠牲型 
他人を優先し、自分を後回しにする。頼られるが疲れやすい。

2 承認追求型 
認められることで価値を感じる。評価への反応が強い。

3 回避型 
衝突やストレスを避ける。距離を取ることで自分を守る。

4 調和維持型 
空気を読み対立を避ける。周囲を優先する。

5 共感吸収型 
他人の感情を受け取りやすい。感情疲労が起きやすい。

6 境界希薄型 
人との境界が弱く、相手の問題を引き受けやすい。

7 過剰責任型 
問題を自分の責任として抱え込みやすい。

8 努力燃焼型 
努力で突破しようとするが燃え尽きやすい。

9 理想追求型 
理想が高く現実とのギャップに苦しみやすい。

10 環境適応型 
環境に合わせる能力が高いが自分を後回しにしやすい。

11 孤立耐久型 
一人で抱えて耐える。相談しない傾向。

12 再出発型 
環境を変えることで流れを変えようとする。

--------------------------------
【出力構造】
--------------------------------
以下のMarkdown形式で出力してください。見出しには必ず「##」を付けてください。

## 人生構造分析レポート

## 0 前提

このレポートは
あなたの人生を評価するものではありません。

回答内容から
あなたが無意識に繰り返している
行動や感情のパターンを
構造として整理したものです。

## 1 主タイプ

12タイプの中から
最も近いタイプを1つ選び
理由を説明してください。

## 2 副タイプ

補助的に強く出ているタイプを
1つ選び理由を書いてください。

## 3 全体構造サマリー

この人の人生で
繰り返されやすい構造をまとめる。

## 4 人生パターン分析

以下の4つを分析

・人間関係 
・仕事 
・感情 
・疲労

## 5 無意識の構造

この人が
無意識に選びやすい思考パターンを説明する。

## 6 強み

この構造タイプの強みを書く。

## 7 課題

この構造タイプが
繰り返しやすい問題を書く。

## 8 変化のヒント

人生パターンを変えるために
今できる行動を3つ書く。

## 9 レポートの限界

ここまで読んで
思い当たることがあったかもしれません。

ただ、このレポートは
「人生の構造を見える形にした地図」です。

地図があっても
実際に歩かなければ
景色は変わりません。

多くの人はここで理解します。

そして
また同じ環境に戻り
同じ反応をしてしまいます。

なぜなら
人生の構造は
理解ではなく
反応として体に残っているからです。

## 10 次の選択

ここで2つの選択があります。

このレポートを
気づきとして持ち帰るか。

それとも
この構造を書き換えていくか。

## 11 次のステップ

現在
人生構造を整理する
個別解析セッションを行っています。

AIレポートでは見えない部分まで含め

・繰り返している構造 
・原因となる思考 
・止めるための行動 

を整理します。

希望する方は
こちらから申し込みできます。

※文字数目安：1200〜1800文字
"""

    user_prompt = f"以下のユーザー回答を分析してください。\n\n【ユーザー回答（10の質問と自分史）】\n{request.formattedHistory}"

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
