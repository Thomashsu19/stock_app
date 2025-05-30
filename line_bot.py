from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from stock import StockApp
from datetime import datetime
import json
from dotenv import load_dotenv
import os

class LineBotApp:
    def __init__(self):
        self.app = Flask(__name__)
        load_dotenv()

        channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
        channel_secret = os.getenv("CHANNEL_SECRET")
        self.line_bot_api = LineBotApi(channel_access_token)
        self.handler = WebhookHandler(channel_secret)
        self.user_states = {}
        self.user_data = {}

        self.stock = StockApp()
        self._setup_routes()
        

    def _setup_routes(self):
        @self.app.route("/callback", methods=['POST'])
        def callback():
            signature = request.headers.get("X-Line-Signature", "")
            body = request.get_data(as_text=True)
            try:
                self.handler.handle(body, signature)
            except InvalidSignatureError:
                abort(400)
            return 'OK'

        @self.handler.add(MessageEvent, message=TextMessage)
        def handle_message(event):
            msg = event.message.text
            user_id = event.source.user_id

            # 處理輸入股票的資訊
            if self.user_states.get(user_id) == "waiting_for_date":
                self._process_data_input(event, msg, user_id)
                return

            # 處理一般訊息
            if msg == '1':
                self._handle_get_stock_data(event)
            elif msg == "2":
                self._handle_waiting_for_date(event, user_id)

    def _process_data_input(self, event, msg, user_id):
        self.user_data[user_id] = msg
        self.user_states[user_id] = None  # 重置狀態

        try:
            date, stock_symbol, price, quantity = msg.split(',')

            date = f"{date[:4]}/{date[4:6]}/{date[6:]}"
            # 驗證日期
            if not self._validate_date(event, date):
                return

            # 驗證其他輸入
            try:
                stock_symbol = stock_symbol.upper()
                price = float(price)
                quantity = float(quantity)
            except ValueError:
                self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="有東西打錯，請重新輸入")
                )
                return

            # 新增股票紀錄
            self.stock.add_stock_record(date, stock_symbol, price, quantity)
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"已新增：{msg}")
            )
        except ValueError:
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="格式錯誤，請輸入正確的格式：日期,股票代號,價格,股數")
            )

    def _validate_date(self, event, date):
        try:
            input_date = datetime.strptime(date, "%Y/%m/%d")
            if input_date > datetime.now():
                raise ValueError("日期不能是未來的日期")
            return True
        except ValueError:
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="日期錯誤，請輸入正確的日期且不能是未來的日期")
            )
            return False

    def _handle_get_stock_data(self, event):
        reply = self.stock.get_stock_data()
        self.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{reply}")
        )

    def _handle_waiting_for_date(self, event, user_id):
        self.user_states[user_id] = "waiting_for_date"
        self.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請輸入購買資訊，先股價再股數（例如：20250625,AAPL,30,20）")
        )

    def run(self, port=8080):
        self.app.run(host="0.0.0.0", port=10000)

