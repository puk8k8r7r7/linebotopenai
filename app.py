from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

import os
import requests
import openai

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')

# OpenAI GPT-3 回應函數
def GPT_response(text):
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    answer = response['choices'][0]['text'].replace('。', '')
    answer = answer.lstrip('?').lstrip()
    return answer

# 取得空氣品質資訊的函數
def get_air_quality():
    # 請將 'YOUR_API_KEY' 替換為實際的 API 金鑰
    api_key = 'YOUR_API_KEY'
    url = 'https://pm25.lass-net.org/API-1.0.0/device/08BEAC0A08AE/latest/?format=JSON'
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # 從回應中提取相關的空氣品質資訊
        pm25 = data['feeds'][0]['s_d0']
        temperature = data['feeds'][0]['s_t0']
        humidity = data['feeds'][0]['s_h0']
        
        air_quality_info = f'空氣品質: PM2.5 {pm25}, 溫度: {temperature}°C, 濕度: {humidity}%'
        return air_quality_info
    except Exception as e:
        print(f"取得空氣品質資訊時發生錯誤: {str(e)}")
        return "取得空氣品質資訊時發生錯誤."

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("請求內容: " + body)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    air_quality_info = get_air_quality()
    gpt_answer = GPT_response(msg)
    
    combined_message = f"{air_quality_info}\n\nGPT-3 回應: {gpt_answer}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(combined_message))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



