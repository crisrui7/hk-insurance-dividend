"""
周大福人寿分红实现率数据爬虫
CTF Life Insurance Dividend Fulfillment Ratio Scraper
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

class CTFScraper:
    def __init__(self):
        self.url = "https://www.ctflife.com.hk/tc/support/important-information/fulfillment-ratios-dividends"
        self.company_name = "周大福人寿"
        self.data_year = 2024  # 报告年度
        
    def fetch_page(self):
        """获取网页内容"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(self.url, headers=headers)
        response.encoding = 'utf-8'
        return response.text
    
    def parse_product_tables(self, html_content):
        """解析产品数据表格"""
        soup = BeautifulSoup(html_content, 'html.parser')
        products_data = []
        
        # 查找所有产品名称（通常在表格前的标题中）
        # 周大福的页面结构：产品名 - 分红人寿保险
        # 然后跟着一个table
        
        # 先找到所有的表格
        tables = soup.find_all('table')
        
        print(f"找到 {len(tables)} 个表格")
        
        for idx, table in enumerate(tables):
            # 尝试找到这个表格对应的产品名称
            # 通常产品名在表格上方的文本中
            product_name = self._find_product_name_for_table(table)
            
            if not product_name:
                print(f"表格 {idx} 无法找到产品名称，跳过")
                continue
            
            # 解析表格数据
            table_data = self._parse_single_table(table, product_name)
            if table_data:
                products_data.extend(table_data)
        
        return products_data
    
    def _find_product_name_for_table(self, table):
        """找到表格对应的产品名称"""
        # 向上查找最近的产品标题
        current = table.find_previous()
        max_search = 10  # 最多向上搜索10个元素
        search_count = 0
        
        while current and search_count < max_search:
            text = current.get_text().strip()
            # 产品名通常包含「」或特定格式
            if '「' in text and '」' in text and '保' in text:
                # 提取产品名（去除后缀如 "- 分红人寿保险"）
                product_name = text.split('-')[0].strip()
                return product_name
            current = current.find_previous()
            search_count += 1
        
        return None
    
    def _parse_single_table(self, table, product_name):
        """解析单个表格"""
        rows = table.find_all('tr')
        if len(rows) < 2:
            return []
        
        # 解析表头
        header_row = rows[0]
        headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
        
        # 数据行
        data_records = []
        for row in rows[1:]:
            cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
            if len(cells) < 2:
                continue
            
            # 第一列通常是类别（週年紅利、終期紅利等）
            category = cells[0] if cells else ""
            # 第二列是货币
            currency = cells[1] if len(cells) > 1 else ""
            
            # 剩余列是各个保单年度的数据
            # 从第3列开始（索引2）到倒数第1列
            for col_idx in range(2, len(cells)):
                # 对应的保单年期
                if col_idx < len(headers):
                    year_header = headers[col_idx]
                    # 提取年份数字（如 "1 (2023)" -> 1）
                    policy_year = self._extract_policy_year(year_header)
                    
                    fulfillment_value = cells[col_idx]
                    
                    # 清洗数据值
                    fulfillment_rate, status = self._parse_fulfillment_value(fulfillment_value)
                    
                    data_records.append({
                        'company': self.company_name,
                        'product_name': product_name,
                        'category': category,  # 週年紅利/復歸紅利/終期紅利等
                        'currency': currency,
                        'policy_year': policy_year,
                        'fulfillment_rate': fulfillment_rate,
                        'status': status,  # 如：已停售、未推出、沒有保單等
                        'data_year': self.data_year,
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    })
        
        return data_records
    
    def _extract_policy_year(self, header_text):
        """从表头提取保单年期数字"""
        # 例如: "1 (2023)" -> 1, "11+ (2013或之前)" -> 11
        match = re.search(r'(\d+)', header_text)
        if match:
            return int(match.group(1))
        return None
    
    def _parse_fulfillment_value(self, value_text):
        """解析分红实现率值"""
        value_text = value_text.strip()
        
        # 如果是百分比
        if '%' in value_text:
            try:
                rate = int(value_text.replace('%', ''))
                return rate, 'normal'
            except:
                return None, value_text
        
        # 特殊状态
        status_mapping = {
            '已停售': 'discontinued',
            '未推出': 'not_launched',
            '沒有保單': 'no_policy',
            '沒有分紅': 'no_dividend',
            '沒有保單終結': 'no_policy_terminated',
            '尚未有保單達至': 'not_yet_reached'
        }
        
        for cn_status, en_status in status_mapping.items():
            if cn_status in value_text:
                return None, en_status
        
        return None, value_text
    
    def save_to_csv(self, data, filename='ctf_dividend_data.csv'):
        """保存数据到CSV"""
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"数据已保存到 {filename}")
        print(f"总共 {len(df)} 条记录")
        return df
    
    def run(self):
        """执行爬取流程"""
        print("开始爬取周大福人寿分红实现率数据...")
        
        # 获取页面
        html = self.fetch_page()
        
        # 解析数据
        products_data = self.parse_product_tables(html)
        
        # 保存数据
        df = self.save_to_csv(products_data)
        
        # 显示统计信息
        print("\n数据统计:")
        print(f"产品数量: {df['product_name'].nunique()}")
        print(f"货币种类: {df['currency'].unique()}")
        print(f"类别: {df['category'].unique()}")
        
        return df

if __name__ == "__main__":
    scraper = CTFScraper()
    df = scraper.run()
    
    # 显示样例数据
    print("\n样例数据:")
    print(df.head(10))
