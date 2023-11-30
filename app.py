import requests
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')

# 即時匯率 API 的 URL
currency_api_url = 'https://tw.rter.info/capi.php'

def get_exchange_rates():
    try:
        response = requests.get(currency_api_url)
        currency_data = response.json()
        return currency_data
    except Exception as e:
        print(f"取得匯率時發生錯誤: {e}")
        return None

def GPT_response(text):
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    answer = response['choices'][0]['text'].replace('。', '')
    answer = answer.lstrip('?').lstrip()
    return answer

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("收到訊息: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.lower()

    # 如果使用者輸入 "exchange rate"，則顯示即時匯率
    if 'exchange rate' in msg:
        exchange_data = get_exchange_rates()
        if exchange_data:
            # 假設您想顯示所有可用的匯率
            exchange_rates_text = "\n".join([f"{currency}: {rate}" for currency, rate in exchange_data.items()])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(exchange_rates_text))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("無法取得即時匯率。"))
    else:
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)

import os

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

