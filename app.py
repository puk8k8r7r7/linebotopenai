from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import traceback
import requests  # 新增引用 requests
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

# 空汙 API 的網址
pm25_api_url = "https://data.moenv.gov.tw/api/v2/aqx_p_02?api_key=1710a1b3-c964-41ad-a1e8-2d7705d5bc84"
# 支援的地區
supported_locations = [
    '臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市',
    '宜蘭縣', '新竹縣', '苗栗縣', '彰化縣', '南投縣', '雲林縣',
    '嘉義縣', '屏東縣', '花蓮縣', '臺東縣', '澎湖縣',
    '基隆市', '新竹市', '嘉義市'
]

def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    
    # 重組回應並替換句號
    answer = response['choices'][0]['text'].replace('。', '')
    
    # 去掉開頭的問號和空格
    answer = answer.lstrip('?').lstrip()
    
    return answer

# 取得空汙資訊的函數
def get_air_quality(location=None):
    try:
        response = requests.get(pm25_api_url)
        data = response.json()

        if 'records' in data:
            records = data['records']
            if records:
                for record in records:
                    site_name = record.get('SiteName', '未知地點')
                    if location and location in site_name:
                        pm25_value = record.get('PM2.5', '未知')
                        return f'{site_name} 的 PM2.5 值為 {pm25_value}'
                return '找不到該地區的空氣品質資料'
            else:
                return '沒有空氣品質資料'
        else:
            return '無法取得空氣品質資訊'

    except Exception as e:
        print(f"Error retrieving air quality: {e}")
        return '無法取得空氣品質資訊'

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text

    # 判斷是否為特定指令
    if '空氣品質' in msg:
        location = None
        for loc in supported_locations:
            if loc in msg:
                location = loc
                break
        air_quality_info = get_air_quality(location)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(air_quality_info))
    else:
        # 使用 GPT-3 生成回應
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

