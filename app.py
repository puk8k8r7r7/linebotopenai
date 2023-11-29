from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import tempfile, os
import datetime
import openai
import time
import traceback
import json, requests
import openai

app = Flask(__name__)
# LINE BOT info
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

cities = ['基隆市', '嘉義市', '臺北市', '嘉義縣', '新北市', '臺南市', '桃園縣', '高雄市', '新竹市', '屏東縣', '新竹縣', '臺東縣', '苗栗縣', '花蓮縣', '臺中市']

def get_weather(city):
    token = 'CWA-4A8C2179-9849-40EB-947F-FD750B13862E'
    url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=' + token + '&format=JSON&locationName=' + str(city)
    Data = requests.get(url)
    Data = (json.loads(Data.text, encoding='utf-8'))['records']['location'][0]['weatherElement']
    res = json.load(open('card.json', 'r', encoding='utf-8'))
    for j in range(3):
        bubble = json.load(open('bubble.json', 'r', encoding='utf-8'))
        # title
        bubble['body']['contents'][0]['text'] = city + '未來 36 小時天氣'
        # time
        bubble['body']['contents'][1]['contents'][0]['text'] = '{} ~ {}'.format(Data[0]['time'][j]['startTime'][5:-3], Data[0]['time'][j]['endTime'][5:-3])
        # weather
        bubble['body']['contents'][3]['contents'][1]['contents'][1]['text'] = Data[0]['time'][j]['parameter']['parameterName']
        # temp
        bubble['body']['contents'][3]['contents'][2]['contents'][1]['text'] = '{}°C ~ {}°C'.format(
            Data[2]['time'][j]['parameter']['parameterName'], Data[4]['time'][j]['parameter']['parameterName'])
        # rain
        bubble['body']['contents'][3]['contents'][3]['contents'][1]['text'] = Data[1]['time'][j]['parameter']['parameterName']
        # comfort
        bubble['body']['contents'][3]['contents'][4]['contents'][1]['text'] = Data[3]['time'][j]['parameter']['parameterName']
        res['contents'].append(bubble)
    return res

# Message event
@handler.add(MessageEvent)
def handle_message(event):
    message_type = event.message.type
    user_id = event.source.user_id
    reply_token = event.reply_token
    if message_type == 'text':
        message = event.message.text
        if message[:2] == '天氣':
            city = message[3:]
            city = city.replace('台', '臺')
            if not (city in cities):
                line_bot_api.reply_message(reply_token, TextSendMessage(text="查詢格式為: 天氣 縣市"))
            else:
                res = get_weather(city)
                line_bot_api.reply_message(reply_token, FlexSendMessage(city + '未來 36 小時天氣預測', res))
        else:
            # 使用 GPT 回答其他問題
            GPT_answer = GPT_response(message)
            print(GPT_answer)
            line_bot_api.reply_message(reply_token, TextSendMessage(GPT_answer))
    elif message_type == 'location':
        city = event.message.address[5:8].replace('台', '臺')
        res = get_weather(city)
        line_bot_api.reply_message(reply_token, FlexSendMessage(city + '未來 36 小時天氣預測', res))

# Flask route for LINE webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port)
