from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import json, requests
import os
import tempfile
import datetime
import openai
import time
import traceback

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# LINE BOT info
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')


# ...

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text

    # GPT response
    GPT_answer = GPT_response(msg)
    print(GPT_answer)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))

    # 天氣查詢功能
    if msg[:2] == '天氣':
        city = msg[3:]
        city = city.replace('台', '臺')
        if not (city in cities):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查詢格式為: 天氣 縣市"))
        else:
            res = get(city)
            line_bot_api.reply_message(event.reply_token, TemplateSendMessage(
                alt_text=city + '未來 36 小時天氣預測',
                template=CarouselTemplate(
                    columns=[
                        CarouselColumn(
                            thumbnail_image_url='https://i.imgur.com/Ex3Opfo.png',
                            title='{} ~ {}'.format(res[0][0]['startTime'][5:-3], res[0][0]['endTime'][5:-3]),
                            text='天氣狀況 {}\n溫度 {} ~ {} °C\n降雨機率 {}'.format(res[0][0]['parameter']['parameterName'],
                                                                       res[0][2]['parameter']['parameterName'],
                                                                       res[0][4]['parameter']['parameterName'],
                                                                       res[0][1]['parameter']['parameterName']),
                            actions=[
                                URIAction(
                                    label='詳細內容',
                                    uri='https://www.cwb.gov.tw/V8/C/W/County/index.html'
                                )
                            ]
                        ) for data in res[0]
                    ]
                )
            ))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))

# ...

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port)
