"""
基于周大福人寿网站结构创建样本数据集
用于MVP开发和测试
"""

import pandas as pd
import sqlite3
from datetime import datetime

def create_sample_dataset():
    """
    创建样本数据集
    基于实际网页结构的真实数据示例
    """
    
    records = []
    
    # 产品列表（从网页中提取的真实产品）
    products = [
        {
            'name': '「传承宝」壽險計劃',
            'type': '分紅人壽保險',
            'currencies': ['美元'],
            'categories': ['週年紅利', '終期紅利']
        },
        {
            'name': '「财富100」壽險計劃',
            'type': '分紅人壽保險',
            'currencies': ['美元'],
            'categories': ['週年紅利', '終期紅利']
        },
        {
            'name': '「小龙 88」壽險計劃',
            'type': '分紅人壽保險',
            'currencies': ['美元'],
            'categories': ['週年紅利', '終期紅利']
        },
        {
            'name': '「守护168」危疾保障計劃 (加強版)',
            'type': '分紅危疾人壽保險',
            'currencies': ['美元'],
            'categories': ['終期紅利']
        },
        {
            'name': '「盛享 • 年金寶」入息計劃',
            'type': '分紅年金保險',
            'currencies': ['美元'],
            'categories': ['週年紅利', '終期紅利']
        },
        {
            'name': '「匠心 • 傳承」儲蓄壽險計劃2（尊尚版）',
            'type': '分紅人壽保險',
            'currencies': ['美元', '港元', '人民幣'],
            'categories': ['復歸紅利', '終期分紅']
        }
    ]
    
    # 模拟数据（基于网页中看到的真实数据模式）
    # 「传承宝」的真实数据示例
    product_data_samples = {
        '「传承宝」壽險計劃': {
            '週年紅利': {
                '美元': {
                    1: ('discontinued', None),  # 已停售
                    2: ('normal', 100),
                    3: ('normal', 100),
                    4: ('normal', 100),
                    5: ('normal', 100),
                    6: ('not_launched', None),  # 未推出
                }
            },
            '終期紅利': {
                '美元': {
                    1: ('discontinued', None),
                    2: ('no_termination', None),  # 沒有保單終結
                    3: ('normal', 100),
                    4: ('normal', 100),
                    5: ('normal', 100),
                    6: ('not_launched', None),
                }
            }
        },
        '「财富100」壽險計劃': {
            '週年紅利': {
                '美元': {i: ('normal', 100) for i in range(1, 12)}
            },
            '終期紅利': {
                '美元': {
                    1: ('no_dividend', None),
                    2: ('no_dividend', None),
                    **{i: ('normal', 100) for i in range(3, 12)}
                }
            }
        },
        '「小龙 88」壽險計劃': {
            '週年紅利': {
                '美元': {
                    1: ('no_dividend', None),
                    2: ('no_dividend', None),
                    3: ('no_dividend', None),
                    4: ('not_launched', None),
                }
            },
            '終期紅利': {
                '美元': {
                    1: ('no_termination', None),
                    2: ('normal', 100),
                    3: ('no_termination', None),
                    4: ('not_launched', None),
                }
            }
        },
        '「匠心 • 傳承」儲蓄壽險計劃2（尊尚版）': {
            '復歸紅利': {
                '美元': {1: ('not_reached_yet', None)},
                '港元': {1: ('not_reached_yet', None)},
                '人民幣': {1: ('not_reached_yet', None)},
            },
            '終期分紅': {
                '美元': {1: ('not_reached_yet', None)},
                '港元': {1: ('not_reached_yet', None)},
                '人民幣': {1: ('not_reached_yet', None)},
            }
        }
    }
    
    # 生成记录
    for product_name, product_data in product_data_samples.items():
        for category, currency_data in product_data.items():
            for currency, year_data in currency_data.items():
                for policy_year, (status, rate) in year_data.items():
                    records.append({
                        'company': '周大福人寿',
                        'product_name': product_name,
                        'product_type': next((p['type'] for p in products if p['name'] == product_name), ''),
                        'category': category,
                        'currency': currency,
                        'policy_year': policy_year,
                        'fulfillment_rate': rate,
                        'status': status,
                        'data_year': 2024,
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    })
    
    return pd.DataFrame(records)


def create_database(df, db_path='/home/claude/insurance_data.db'):
    """创建SQLite数据库并导入数据"""
    
    conn = sqlite3.connect(db_path)
    
    # 创建表
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS fulfillment_ratios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        product_name TEXT NOT NULL,
        product_type TEXT,
        category TEXT NOT NULL,
        currency TEXT NOT NULL,
        policy_year INTEGER NOT NULL,
        fulfillment_rate INTEGER,
        status TEXT,
        data_year INTEGER NOT NULL,
        last_updated TEXT NOT NULL,
        UNIQUE(company, product_name, category, currency, policy_year, data_year)
    )
    """
    
    conn.execute(create_table_sql)
    
    # 导入数据
    df.to_sql('fulfillment_ratios', conn, if_exists='replace', index=False)
    
    # 创建索引
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_product 
        ON fulfillment_ratios(product_name)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_year 
        ON fulfillment_ratios(policy_year)
    """)
    
    conn.commit()
    conn.close()
    
    print(f"数据库已创建: {db_path}")
    print(f"总记录数: {len(df)}")


def main():
    """主函数"""
    print("=" * 60)
    print("周大福人寿分红实现率数据集生成器")
    print("=" * 60)
    
    # 创建数据集
    print("\n1. 生成样本数据...")
    df = create_sample_dataset()
    
    # 显示统计信息
    print(f"\n数据统计:")
    print(f"  - 总记录数: {len(df)}")
    print(f"  - 产品数量: {df['product_name'].nunique()}")
    print(f"  - 货币种类: {', '.join(df['currency'].unique())}")
    print(f"  - 类别: {', '.join(df['category'].unique())}")
    
    # 保存CSV
    csv_path = '/home/claude/ctf_sample_data.csv'
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n2. CSV已保存: {csv_path}")
    
    # 创建数据库
    print("\n3. 创建SQLite数据库...")
    create_database(df)
    
    # 显示样例数据
    print("\n4. 样例数据:")
    print(df.head(10).to_string())
    
    # 按产品分组统计
    print("\n5. 各产品记录数:")
    print(df.groupby('product_name').size())
    
    return df


if __name__ == "__main__":
    df = main()
