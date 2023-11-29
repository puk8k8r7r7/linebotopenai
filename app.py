from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import json
import requests
import openai
import os

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')
# 氣象局 API Key
weather_api_key = 'CWA-4A8C2179-9849-40EB-947F-FD750B13862E'

cities = ['基隆市', '嘉義市', '臺北市', '嘉義縣', '新北市', '臺南市', '桃園縣', '高雄市', '新竹市', '屏東縣', '新竹縣', '臺東縣', '苗栗縣', '花蓮縣', '臺中市']

def get_weather(city):
    url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={weather_api_key}&format=JSON&locationName={city}'
    response = requests.get(url)
    data = response.json()['records']['location'][0]['weatherElement']

    res = {'contents': []}

    for j in range(3):
        bubble = {
            'type': 'bubble',
            'hero': {
                'type': 'image',
                'url': 'https://i.imgur.com/Ex3Opfo.png',
                'size': 'full',
                'aspectRatio': '20:13',
                'aspectMode': 'cover',
            },
            'body': {
                'type': 'box',
                'layout': 'vertical',
                'contents': [
                    {
                        'type': 'text',
                        'text': f'{city}未來 36 小時天氣',
                        'weight': 'bold',
                        'size': 'xl',
                    },
                    {
                        'type': 'box',
                        'layout': 'vertical',
                        'margin': 'lg',
                        'spacing': 'sm',
                        'contents': [
                            {
                                'type': 'box',
                                'layout': 'baseline',
                                'spacing': 'sm',
                                'contents': [
                                    {
                                        'type': 'text',
                                        'text': f'{data[0]["time"][j]["startTime"][5:-3]} ~ {data[0]["time"][j]["endTime"][5:-3]}',
                                        'flex': 0,
                                        'size': 'sm',
                                        'color': '#AAAAAA',
                                    },
                                ],
                            },
                            {
                                'type': 'box',
                                'layout': 'baseline',
                                'spacing': 'sm',
                                'contents': [
                                    {
                                        'type': 'text',
                                        'text': f'天氣狀況 {data[0]["time"][j]["parameter"]["parameterName"]}',
                                        'flex': 0,
                                        'size': 'sm',
                                        'color': '#AAAAAA',
                                    },
                                ],
                            },
                            {
                                'type': 'box',
                                'layout': 'baseline',
                                'spacing': 'sm',
                                'contents': [
                                    {
                                        'type': 'text',
                                        'text': f'溫度 {data[2]["time"][j]["parameter"]["parameterName"]} ~ {data[4]["time"][j]["parameter"]["parameterName"]} °C',
                                        'flex': 0,
                                        'size': 'sm',
                                        'color': '#AAAAAA',
                                    },
                                ],
                            },
                            {
                                'type': 'box',
                                'layout': 'baseline',
                                'spacing': 'sm',
                                'contents': [
                                    {
                                        'type': 'text',
                                        'text': f'降雨機率 {data[1]["time"][j]["parameter"]["parameterName"]}',
                                        'flex': 0,
                                        'size': 'sm',
                                        'color': '#AAAAAA',
                                    },
                                ],
                            },
                            {
                                'type': 'box',
                                'layout': 'baseline',
                                'spacing': 'sm',
                                'contents': [
                                    {
                                        'type': 'text',
                                        'text': f'舒適度 {data[3]["time"][j]["parameter"]["parameterName"]}',
                                        'flex': 0,
                                        'size': 'sm',
                                        'color': '#AAAAAA',
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        }

        res['contents'].append(bubble)

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
    message_type = event.message.type
    user_id = event.source.user_id
    reply_token = event.reply_token
    message = event.message.text
    if message_type == 'text':
        if message.startswith('天氣'):
            city = message[3:]
            city = city.replace('台', '臺')
            if city not in cities:
                line_bot_api.reply_message(reply_token, TextSendMessage(text="查詢格式為: 天氣 縣市"))
            else:
                res = get_weather(city)
                line_bot_api.reply_message(reply_token, FlexSendMessage(f'{city}未來 36 小時天氣預測', res))
        else:
            GPT_answer = GPT_response(message)
            print(GPT_answer)
            line_bot_api.reply_message(reply_token, TextSendMessage(GPT_answer))
    elif message_type == 'location':
        city = event.message.address[5:8].replace('台', '臺')
        res = get_weather(city)
        line_bot_api.reply_message(reply_token, FlexSendMessage(f'{city}未來 36 小時天氣預測', res))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
