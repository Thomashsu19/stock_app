import pygsheets
import requests
import json
from dotenv import load_dotenv
import os
class StockApp:
    def __init__(self):
        # 授權並打開 Google Sheet
        load_dotenv()
        self.gc = pygsheets.authorize(service_file='credentials.json')
        self.sht = self.gc.open_by_url('https://docs.google.com/spreadsheets/d/1YF-NVd2znu1k8YwVTXbR2CCVCX4hKQGZWzn2XnVQSNs/edit?gid=0#gid=0')
        self.wks = self.sht[0]  # 取第一個工作表
        self.wks2 = self.sht[1]  # 取第二個工作表
        self.finn_hub_api_key = os.getenv("FINN_HUB_API_KEY")

    def add_stock_record(self, date, stock_code, purchase_price, quantity):
        # 準備要新增的列資料
        new_row = [date, stock_code, purchase_price, quantity]

        # 找出目前有幾列資料（從 A 欄非空格數）
        num_rows = len(self.wks.get_col(1, include_empty=False))
        
        # 插入新的一列（加在最後一列之後）
        self.wks.insert_rows(num_rows, number=1, values=new_row)
        print("✅ 資料已成功新增至最後一列")

    def get_price(self):
        # 從 Google Sheet 的 B 欄第二列開始讀取股票代號
        symbols = self.wks.get_col(2, include_empty=False)[1:]  # 跳過第一列標題
        unique_symbols = list(set(symbols))  # 去除重複的股票代號

        # 建立一個字典來儲存每個股票代號的現價
        stock_prices = {}

        for symbol in unique_symbols:
            url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finn_hub_api_key}'
            response = requests.get(url)
            stock_data = response.json()  # {'c': 現價, 'h': 高, 'l': 低, 'o': 開盤, 'pc': 昨收}
            current_price = stock_data.get('c')

            if current_price is not None:
                stock_prices[symbol] = current_price
                print(f"✅ 股票代號: {symbol}, 現價已取得: {current_price}")
            else:
                print(f"⚠️ 無法取得股票代號 {symbol} 的現價")

        # 3. 對應 symbols -> 對應價格，組成一個新列表
        updated_prices = [[stock_prices.get(symbol, "")] for symbol in symbols]

        # 4. 一次性更新 E 欄（第五欄），從第 2 列開始
        start_row = 2
        end_row = start_row + len(updated_prices) - 1
        price_range = f"E{start_row}:E{end_row}"
        self.wks.update_values(price_range, updated_prices)

        print(f"✅ 所有現價已一次性更新至 E 欄（第 {start_row} 列到第 {end_row} 列）")

    def renew_total_page(self):

        self.get_price()  # 更新價格

        # 從 self.wks 讀取資料
        data = self.wks.get_all_records()

        # 建立一個字典來儲存每個股票代號的加總結果
        stock_summary = {}

        for row in data:
            stock_code = row['code']
            quantity = row['quantity']
            purchase_price = row['purchase_price']
            price = row['price']

            if stock_code not in stock_summary:
                stock_summary[stock_code] = {'total_quantity': 0, 'total_cost': 0, 'price': price}
            stock_summary[stock_code]['total_quantity'] += quantity
            stock_summary[stock_code]['total_cost'] += purchase_price * quantity

        # 準備要插入 self.wks2 的資料
        summary_data = []
        for stock_code, summary in stock_summary.items():
            total_quantity = summary['total_quantity']
            avg_price = summary['total_cost'] / total_quantity if total_quantity > 0 else 0
            price = summary['price']
            roi = f"{((price / avg_price) - 1)*100:.4f}%"
            total_return = (price - avg_price) * total_quantity
            summary_data.append([stock_code, avg_price, total_quantity, price, roi, total_return])

        # 清空 self.wks2 並插入新的加總資料
        self.wks2.clear()
        self.wks2.update_values('A1', [['stock_code', 'buying_price', 'quantity', 'price', 'roi', 'total_return']] + summary_data)
        print("✅ 股票加總結果已成功更新至第二個工作表")

    def get_stock_data(self):
        self.renew_total_page()  # 更新總頁面
        # 從 Google Sheet 的 B 欄第二列開始讀取股票代號
        symbols = self.wks2.get_all_records()
        result = []
        headers = ['代號', '買進價', '股數', '價格', '報酬率', '總報酬']
        result.append(f"{headers[0]:<12}{headers[1]:<15}{headers[2]:<10}{headers[3]:<10}{headers[4]:<10}{headers[5]:<15}")
        result.append('-' * 64)
        for row in symbols:
            result.append(f"{row['stock_code']:<12}{row['buying_price']:<15.2f}{row['quantity']:<10}{row['price']:<10.2f}{row['roi']:<10}{row['total_return']:<15.2f}\n")
        return '\n'.join(result)
