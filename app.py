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
import json
import requests
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')
# 天氣API 設定
cwb_api_key = os.getenv('CWB_API_KEY')
cities = ['基隆市', '嘉義市', '臺北市', '嘉義縣', '新北市', '臺南市', '桃園縣', '高雄市', '新竹市', '屏東縣', '新竹縣', '臺東縣', '苗栗縣', '花蓮縣', '臺中市', '宜蘭縣', '彰化縣', '澎湖縣', '南投縣', '金門縣', '雲林縣', '連江縣']

def get_weather(city):
    url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={cwb_api_key}&format=JSON&locationName={city}'
    data = requests.get(url).json()
    weather_data = data['records']['location'][0]['weatherElement']
    return weather_data

def get_weather(city):
    url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={CWB_API_KEY}&format=JSON&locationName={city}'
    data = requests.get(url).json()
    weather_data = data['records']['location'][0]['weatherElement']
    return weather_data

def format_weather_message(city, weather_data):
    message = f"{city}未來36小時天氣預測：\n"
    for entry in weather_data:
        time_period = entry['time'][0]['startTime'][5:-3] + ' ~ ' + entry['time'][0]['endTime'][5:-3]
        weather_condition = entry['time'][0]['parameter']['parameterName']
        temperature_min = entry['time'][2]['parameter']['parameterName']
        temperature_max = entry['time'][4]['parameter']['parameterName']
        rain_probability = entry['time'][1]['parameter']['parameterName']
        
        message += f"\n時間：{time_period}\n天氣狀況：{weather_condition}\n溫度：{temperature_min} ~ {temperature_max} °C\n降雨機率：{rain_probability}\n"
    
    return message

def GPT_response(text):
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    answer = response['choices'][0]['text'].replace('。', '')
    answer = answer.lstrip('?').lstrip()
    return answer

def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    
    # 重組回應並替換句號
    answer = response['choices'][0]['text'].replace('。', '')
    
    # 去掉開頭的問號和空格
    answer = answer.lstrip('?').lstrip()
    
    return answer

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
    if msg.startswith('天氣'):
        city = msg[3:]
        city = city.replace('台', '臺')
        if city not in cities:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查詢格式為: 天氣 縣市"))
        else:
            weather_data = get_weather(city)
            weather_message = format_weather_message(city, weather_data)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=weather_message))
    else:
        # 如果不是查詢天氣，則使用 GPT 回應
        GPT_answer = GPT_response(msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))

@handler.add(PostbackEvent)
def handle_postback(event):
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

