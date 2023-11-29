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

# Weather API token
weather_token = 'CWA-4A8C2179-9849-40EB-947F-FD750B13862E'
weather_url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001'

def get_weather(city):
    headers = {'Authorization': weather_token}
    params = {'format': 'JSON', 'locationName': city}
    response = requests.get(weather_url, headers=headers, params=params)
    data = response.json()['records']['location'][0]['weatherElement']
    
    res = [[] , [] , []]
    for j in range(3):
        for i in data:
            res[j].append(i['time'][j])
    return res

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
        if not (city in cities):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查詢格式為: 天氣 縣市"))
        else:
            weather_data = get_weather(city)
            line_bot_api.reply_message(event.reply_token, TemplateSendMessage(
                alt_text=f'{city}未來 36 小時天氣預測',
                template=CarouselTemplate(
                    columns=[
                        CarouselColumn(
                            thumbnail_image_url='https://i.imgur.com/Ex3Opfo.png',
                            title='{} ~ {}'.format(weather_data[0][0]['startTime'][5:-3], weather_data[0][0]['endTime'][5:-3]),
                            text='天氣狀況 {}\n溫度 {} ~ {} °C\n降雨機率 {}'.format(
                                data[0]['parameter']['parameterName'], data[2]['parameter']['parameterName'],
                                data[4]['parameter']['parameterName'], data[1]['parameter']['parameterName']),
                            actions=[
                                URIAction(
                                    label='詳細內容',
                                    uri='https://www.cwb.gov.tw/V8/C/W/County/index.html'
                                )
                            ]
                        ) for data in weather_data
                    ]
                )
            ))
    else:
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
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

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

