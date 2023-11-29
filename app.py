from flask import Flask, request, abort, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
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

# 支援的城市列表
cities = ['基隆市', '嘉義市', '臺北市', '嘉義縣', '新北市', '臺南市', '桃園縣', '高雄市', '新竹市', '屏東縣', '新竹縣', '臺東縣', '苗栗縣', '花蓮縣', '臺中市']

# 空氣品質查詢函數
def get_air_quality(city):
    url = f'https://data.moenv.gov.tw/api/v1/aqx_p_02?format=json&offset=0&limit=5&api_key=1710a1b3-c964-41ad-a1e8-2d7705d5bc84'
    response = requests.get(url)
    data = response.json()
    air_quality = data['data'][0]['AQI']
    return air_quality
    
# OPENAI GPT 回應函數
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
        if city in cities:
            air_quality = get_air_quality(city)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{city}的空氣品質指數（AQI）為：{air_quality}"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查詢格式為: 天氣 縣市"))
    else:
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
