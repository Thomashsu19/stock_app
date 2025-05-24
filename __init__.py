from stock import StockApp
from line_bot import LineBotApp
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage


# stock = StockApp()
bot = LineBotApp()
# stock.add_stock_record("2025/06/25", "AAPL", 18, 20)