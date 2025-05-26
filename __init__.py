from stock import StockApp
from line_bot import LineBotApp
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

if __name__ == "__main__":
    bot = LineBotApp()
    bot.run(port=5050)

# stock = StockApp()
# bot = LineBotApp()
# stock.add_stock_record("2025/06/25", "AAPL", 18, 20)