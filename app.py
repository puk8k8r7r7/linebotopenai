import requests
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import os
import openai

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')

# 故事 API 的 URL
story_api_url = 'https://api.topthink.com/wiki/story'

def get_random_story():
    try:
        response = requests.get(story_api_url)
        story_data = response.json()  # 假設 API 回傳的是 JSON 格式的故事列表
        # 從回傳的故事中隨機選擇一個
        story = random.choice(story_data['data'])
        return story['title'] + '\n' + story['content']
    except Exception as e:
        print(f"取得故事時發生錯誤: {e}")
        return None

# ...

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if '健康小幫手' in msg:
        health_info = health_assistant(msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(health_info))
    elif '故事' in msg:
        # 使用故事功能
        story = get_random_story()
        if story:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(story))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("無法取得故事，請稍後再試。"))
    else:
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))

# ...

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
