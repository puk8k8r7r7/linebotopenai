from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import os

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')

def GPT_response(text):
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    answer = response['choices'][0]['text'].replace('。', '')
    answer = answer.lstrip('?').lstrip()
    return answer

# 新增健康小幫手功能
def health_assistant(command):
    if '健康' in command:
        return "維持良好的健康非常重要，請保持適量的運動、均衡的飲食和充足的睡眠。如果有特殊健康需求，建議諮詢專業醫生的建議。"
    elif '運動' in command:
        return "每天適量的運動有助於保持身體健康。可以嘗試每天散步、慢跑或其他有氧運動。"
    elif '飲食' in command:
        return "保持均衡的飲食，攝取足夠的蔬菜、水果、蛋白質和維生素。減少高油、高糖和高鹽食物的攝取。"
    elif '睡眠' in command:
        return "確保每天有足夠的睡眠時間，成年人通常需要7-8小時的睡眠。維持規律的睡眠時間有助於身體恢復和健康。"
    else:
        return "請輸入'健康'、'運動'、'飲食'或'睡眠'來獲得相關健康資訊。"

# 監聽所有來自 /callback 的 Post Request
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

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if '健康小幫手' in msg:
        # 使用健康小幫手功能
        health_info = health_assistant(msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(health_info))
    else:
        # 使用 GPT-3 生成回應
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))

@handler.add(PostbackEvent)
def handle_message(event):
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
