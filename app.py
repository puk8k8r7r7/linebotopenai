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
import os
import openai

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# LINE BOT info
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
cities = ['基隆市', '嘉義市', '臺北市', '嘉義縣', '新北市', '臺南市', '桃園縣', '高雄市', '新竹市', '屏東縣', '新竹縣', '臺東縣', '苗栗縣', '花蓮縣', '臺中市', '宜蘭縣', '彰化縣', '澎湖縣', '南投縣', '金門縣', '雲林縣', '連江縣']

# OpenAI API Key
openai.api_key = os.getenv('OPENAI_API_KEY')

def GPT_response(text):
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    answer = response['choices'][0]['text'].replace('。', '')
    answer = answer.lstrip('?').lstrip()
    return answer

def get_weather(city):
    token = os.getenv('OPEN_DATA_API_TOKEN')
    url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={str(city)}'
    Data = requests.get(url)
    Data = (json.loads(Data.text, encoding='utf-8'))['records']['location'][0]['weatherElement']
    res = [[], [], []]
    for j in range(3):
        for i in Data:
            res[j].append(i['time'][j])
    return res

# Message event
@handler.add(MessageEvent)
def handle_message(event):
    message_type = event.message.type
    user_id = event.source.user_id
    reply_token = event.reply_token
    message = event.message.text
    
    if message[:2] == '天氣':
        city = message[3:]
        city = city.replace('台', '臺')
        
        if not (city in cities):
            line_bot_api.reply_message(reply_token, TextSendMessage(text="查詢格式為: 天氣 縣市"))
        else:
            res = get_weather(city)
            line_bot_api.reply_message(reply_token, TemplateSendMessage(
                alt_text=city + '未來 36 小時天氣預測',
                template=CarouselTemplate(
                    columns=[
                        CarouselColumn(
                            thumbnail_image_url='https://i.imgur.com/Ex3Opfo.png',
                            title='{} ~ {}'.format(res[0][0]['startTime'][5:-3], res[0][0]['endTime'][5:-3]),
                            text='天氣狀況 {}\n溫度 {} ~ {} °C\n降雨機率 {}'.format(
                                data[0]['parameter']['parameterName'],
                                data[2]['parameter']['parameterName'],
                                data[4]['parameter']['parameterName'],
                                data[1]['parameter']['parameterName']),
                            actions=[
                                URIAction(
                                    label='詳細內容',
                                    uri='https://www.cwb.gov.tw/V8/C/W/County/index.html'
                                )
                            ]
                        ) for data in res
                    ]
                )
            ))
    else:
        GPT_answer = GPT_response(message)
        print(GPT_answer)
        line_bot_api.reply_message(reply_token, TextSendMessage(GPT_answer))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    print(body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port)

