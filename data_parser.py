"""
数据解析和清洗模块
Data Parser and Cleaner for Insurance Dividend Fulfillment Ratios
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class DataParser:
    """统一的数据解析器"""
    
    # 状态码映射
    STATUS_MAPPING = {
        'closed to sales': 'discontinued',
        'n/a(1)': 'not_launched',
        'n/a': 'no_data',
        'no dividend': 'no_dividend',
        'no termination': 'no_termination',
        'not reached yet': 'not_reached_yet',
        'no policy': 'no_policy',
    }
    
    # 货币映射
    CURRENCY_MAPPING = {
        '美元': 'USD',
        '港元': 'HKD',
        '港幣': 'HKD',
        '人民币': 'RMB',
        '人民幣': 'RMB',
        'usd': 'USD',
        'hkd': 'HKD',
        'rmb': 'RMB',
        'cny': 'RMB',
        '所有': 'ALL',
    }
    
    # 分红类别映射
    CATEGORY_MAPPING = {
        'dividend': '週年紅利',
        'terminal bonus': '終期紅利',
        'reversionary bonus': '歸原紅利',
        'special bonus': '特別紅利',
        '週年紅利': '週年紅利',
        '终期红利': '終期紅利',
        '終期紅利': '終期紅利',
        '归原红利': '歸原紅利',
        '歸原紅利': '歸原紅利',
        '特别红利': '特別紅利',
        '特別紅利': '特別紅利',
    }
    
    def __init__(self, data_year: int = 2024):
        self.data_year = data_year
        self.last_updated = datetime.now().strftime('%Y-%m-%d')
    
    def parse_ctf(self, json_file: str) -> List[Dict[str, Any]]:
        """解析周大福JSON数据"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        records = []
        for item in data.get('fulfillment_ratios', []):
            # 提取产品名称（去除状态标识）
            product_name = item.get('product_name', '')
            product_name = re.sub(r'\s*\(Closed to sales\)\s*', '', product_name, flags=re.IGNORECASE)
            product_name = product_name.strip()
            
            # 提取货币
            currency = self._normalize_currency(item.get('currency', ''))
            
            # 提取购买年份（周大福的policy_year就是购买年份）
            purchase_year = item.get('policy_year', None)
            policy_year = None  # 周大福数据不包含保单年期信息
            
            # 提取分红实现率
            ratio = item.get('ratio')
            if ratio is not None:
                fulfillment_rate = int(ratio * 100)  # 转换为百分比
                status = 'normal'
            else:
                fulfillment_rate = None
                status = 'no_data'
            
            # 提取分红类别
            category = self._normalize_category(item.get('type', 'Dividend'))
            
            record = {
                'company': '周大福人寿',
                'product_name': product_name,
                'product_type': None,
                'category': category,
                'currency': currency,
                'policy_year': policy_year,
                'purchase_year': purchase_year,  # 周大福数据包含购买年份
                'fulfillment_rate': fulfillment_rate,
                'status': status,
                'data_year': self.data_year,
                'last_updated': self.last_updated,
                'data_source': item.get('product_name_citation', '')
            }
            records.append(record)
        
        return records
    
    def parse_aia(self, json_file: str) -> List[Dict[str, Any]]:
        """解析友邦JSON数据"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        records = []
        
        # 处理两种类型的数据
        for data_type in ['fulfillment_ratio_for_dividend_bonus', 'fulfillment_ratio_for_total_value']:
            items = data.get(data_type, [])
            
            # 确定分红类别
            if 'dividend_bonus' in data_type:
                default_category = '週年紅利'
            else:
                default_category = '總現金價值'
            
            for item in items:
                # 提取产品名称
                product_name = item.get('product_name', '').strip()
                
                # 提取货币
                currency_raw = item.get('currency', '所有')
                currency = self._normalize_currency(currency_raw)
                
                # 解析保单年期和购买年份
                policy_year_str = item.get('policy_year', '')
                policy_year, purchase_year = self._parse_aia_policy_year(policy_year_str)
                
                # 解析分红实现率
                ratio_str = item.get('fulfillment_ratio', '')
                fulfillment_rate, status = self._parse_ratio_string(ratio_str)
                
                record = {
                    'company': '友邦保险',
                    'product_name': product_name,
                    'product_type': None,
                    'category': default_category,
                    'currency': currency,
                    'policy_year': policy_year,
                    'purchase_year': purchase_year,
                    'fulfillment_rate': fulfillment_rate,
                    'status': status,
                    'data_year': self.data_year,
                    'last_updated': self.last_updated,
                    'data_source': item.get('product_name_citation', '')
                }
                records.append(record)
        
        return records
    
    def parse_prudential(self, json_file: str) -> List[Dict[str, Any]]:
        """解析保诚JSON数据"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        records = []
        
        for product in data.get('prudential_products', []):
            # 解析产品名称（包含货币和类别信息）
            product_name_raw = product.get('product_name', '')
            product_name, currency, category = self._parse_prudential_product_name(product_name_raw)
            
            # 遍历每个年期的数据
            for ratio_item in product.get('fulfillment_ratios', []):
                # 解析保单年期和购买年份
                policy_year_str = ratio_item.get('policy_year', '')
                policy_year, purchase_year = self._parse_prudential_policy_year(policy_year_str)
                
                # 解析分红实现率
                percentage_str = ratio_item.get('percentage', '')
                fulfillment_rate, status = self._parse_ratio_string(percentage_str)
                
                record = {
                    'company': '保诚保险',
                    'product_name': product_name,
                    'product_type': None,
                    'category': category,
                    'currency': currency,
                    'policy_year': policy_year,
                    'purchase_year': purchase_year,
                    'fulfillment_rate': fulfillment_rate,
                    'status': status,
                    'data_year': self.data_year,
                    'last_updated': self.last_updated,
                    'data_source': product.get('product_name_citation', '')
                }
                records.append(record)
        
        return records
    
    def _normalize_currency(self, currency: str) -> str:
        """标准化货币代码"""
        currency_lower = currency.lower().strip()
        return self.CURRENCY_MAPPING.get(currency_lower, currency.upper())
    
    def _normalize_category(self, category: str) -> str:
        """标准化分红类别"""
        category_lower = category.lower().strip()
        return self.CATEGORY_MAPPING.get(category_lower, category)
    
    def _parse_ratio_string(self, ratio_str: str) -> tuple[Optional[int], str]:
        """解析分红实现率字符串"""
        if not ratio_str or ratio_str.strip() == '':
            return None, 'no_data'
        
        ratio_str = ratio_str.strip().lower()
        
        # 检查是否是状态码
        for key, status in self.STATUS_MAPPING.items():
            if key in ratio_str:
                return None, status
        
        # 尝试提取数字
        match = re.search(r'(\d+(?:\.\d+)?)\s*%?', ratio_str)
        if match:
            value = float(match.group(1))
            return int(value), 'normal'
        
        return None, 'no_data'
    
    def _parse_aia_policy_year(self, policy_year_str: str) -> tuple[int, Optional[int]]:
        """解析友邦保单年期字符串
        
        示例: "第一個保單年度 (2023)" -> (1, 2023)
              "第十個保單年度+ (2014之前)" -> (10, 2014)
        """
        # 提取年份
        year_match = re.search(r'\((\d{4})', policy_year_str)
        year_value = int(year_match.group(1)) if year_match else None
        
        # 提取保单年期数字
        chinese_numbers = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
        
        # 尝试匹配"第X個"
        for chinese, number in chinese_numbers.items():
            if f'第{chinese}個' in policy_year_str:
                return number, year_value
        
        # 匹配"第十X個"
        if '第十' in policy_year_str:
            if '第十一' in policy_year_str:
                return 11, year_value
            elif '第十二' in policy_year_str:
                return 12, year_value
            elif '第十三' in policy_year_str:
                return 13, year_value
            elif '第十四' in policy_year_str:
                return 14, year_value
            elif '第十五' in policy_year_str:
                return 15, year_value
            else:
                return 10, year_value
        
        # 匹配数字
        number_match = re.search(r'(\d+)', policy_year_str)
        if number_match:
            return int(number_match.group(1)), year_value
        
        return 0, year_value
    
    def _parse_prudential_policy_year(self, policy_year_str: str) -> tuple[int, Optional[int]]:
        """解析保诚保单年期字符串
        
        示例: "1 (2023)" -> (1, 2023)
              "10+ (2014 之前)" -> (10, 2014)
        """
        # 提取购买年份
        year_match = re.search(r'\((\d{4})', policy_year_str)
        purchase_year = int(year_match.group(1)) if year_match else None
        
        # 提取保单年期数字
        match = re.search(r'(\d+)', policy_year_str)
        policy_year = int(match.group(1)) if match else 0
        
        return policy_year, purchase_year
    
    def _parse_prudential_product_name(self, product_name_raw: str) -> tuple[str, str, str]:
        """解析保诚产品名称
        
        示例: "「理想人生」保障系列 II - 分期繳費 (美元) [2024 報告年度的歸原紅利現金價值分紅實現率]"
        返回: ("「理想人生」保障系列 II", "USD", "歸原紅利")
        """
        # 提取货币
        currency = 'USD'
        currency_match = re.search(r'\((美元|港元|港幣|人民币|人民幣)\)', product_name_raw)
        if currency_match:
            currency = self._normalize_currency(currency_match.group(1))
        
        # 提取分红类别
        category = '週年紅利'  # 默认
        if '歸原紅利' in product_name_raw or '归原红利' in product_name_raw:
            category = '歸原紅利'
        elif '特別紅利' in product_name_raw or '特别红利' in product_name_raw:
            category = '特別紅利'
        elif '終期紅利' in product_name_raw or '终期红利' in product_name_raw:
            category = '終期紅利'
        
        # 提取产品名称（去除货币和类别信息）
        product_name = re.sub(r'\s*\([^)]*\)\s*', ' ', product_name_raw)
        product_name = re.sub(r'\s*\[[^\]]*\]\s*', '', product_name)
        product_name = re.sub(r'\s*-\s*分期繳費\s*', '', product_name)
        product_name = re.sub(r'\s*-\s*整付保費\s*', '', product_name)
        product_name = product_name.strip()
        
        return product_name, currency, category


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_record(record: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证单条记录"""
        errors = []
        
        # 必填字段检查
        required_fields = ['company', 'product_name', 'category', 'currency', 
                          'status', 'data_year']
        for field in required_fields:
            if not record.get(field):
                errors.append(f"缺少必填字段: {field}")
        
        # policy_year和purchase_year至少要有一个
        if record.get('policy_year') is None and record.get('purchase_year') is None:
            errors.append("缺少policy_year或purchase_year")
        
        # 数据类型检查
        if record.get('policy_year') is not None and not isinstance(record.get('policy_year'), int):
            errors.append("policy_year必须是整数或None")
        
        if record.get('purchase_year') is not None and not isinstance(record.get('purchase_year'), int):
            errors.append("purchase_year必须是整数或None")
        
        if record.get('fulfillment_rate') is not None:
            if not isinstance(record['fulfillment_rate'], int):
                errors.append("fulfillment_rate必须是整数或None")
            elif record['fulfillment_rate'] < 0 or record['fulfillment_rate'] > 500:
                errors.append(f"fulfillment_rate值异常: {record['fulfillment_rate']}")
        
        # 逻辑检查
        if record.get('status') == 'normal' and record.get('fulfillment_rate') is None:
            errors.append("状态为normal但fulfillment_rate为空")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_batch(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量验证记录"""
        total = len(records)
        valid = 0
        invalid = 0
        errors_summary = []
        
        for i, record in enumerate(records):
            is_valid, errors = DataValidator.validate_record(record)
            if is_valid:
                valid += 1
            else:
                invalid += 1
                if invalid <= 10:  # 只记录前10个错误
                    errors_summary.append({
                        'record_index': i,
                        'product_name': record.get('product_name'),
                        'errors': errors
                    })
        
        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'errors': errors_summary
        }


def main():
    """测试函数"""
    parser = DataParser(data_year=2024)
    
    # 测试解析
    print("开始解析数据...")
    
    ctf_records = parser.parse_ctf('/home/ubuntu/upload/pasted_file_WdsFng_extract-data-2026-02-12（ctf）.json')
    print(f"✅ 周大福: {len(ctf_records)} 条记录")
    
    aia_records = parser.parse_aia('/home/ubuntu/upload/pasted_file_liy7Iv_extract-data-2026-02-12(aia).json')
    print(f"✅ 友邦: {len(aia_records)} 条记录")
    
    pru_records = parser.parse_prudential('/home/ubuntu/upload/pasted_file_RiSJTW_extract-data-2026-02-12(prudential).json')
    print(f"✅ 保诚: {len(pru_records)} 条记录")
    
    # 验证数据
    print("\n开始验证数据...")
    all_records = ctf_records + aia_records + pru_records
    validation_result = DataValidator.validate_batch(all_records)
    
    print(f"\n验证结果:")
    print(f"  总记录数: {validation_result['total']}")
    print(f"  有效记录: {validation_result['valid']}")
    print(f"  无效记录: {validation_result['invalid']}")
    
    if validation_result['errors']:
        print(f"\n前{len(validation_result['errors'])}个错误:")
        for error in validation_result['errors']:
            print(f"  - 记录{error['record_index']}: {error['product_name']}")
            for e in error['errors']:
                print(f"    {e}")


if __name__ == '__main__':
    main()
