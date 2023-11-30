from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, MessageEvent, TextSendMessage, MemberJoinedEvent
import os
import openai
import requests

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')

# Function to get air quality
def get_air_quality(city):
    # Replace the API_KEY with your actual API key
    api_key = '1710a1b3-c964-41ad-a1e8-2d7705d5bc84'
    url = f'https://data.moenv.gov.tw/api/v1/aqx_p_02?format=json&offset=0&limit=5&api_key={api_key}&city={city}'
    response = requests.get(url)
    data = response.json()
    air_quality = data['data']['aqi']
    return air_quality

# Function to get GPT response
def GPT_response(text):
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    answer = response['choices'][0]['text'].replace('。', '').lstrip('?').lstrip()
    return answer

# Callback route
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

# Handle text messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    
    if msg.startswith('天氣'):
        city = msg[3:].replace('台', '臺')
        air_quality = get_air_quality(city)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{city}的空氣品質指數（AQI）為：{air_quality}"))
    else:
        gpt_answer = GPT_response(msg)
        print(gpt_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(gpt_answer))

# Handle member joined event
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


