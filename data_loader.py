"""
数据库加载器模块
Database Loader for Insurance Dividend Fulfillment Ratios
"""

import sqlite3
import os
from typing import List, Dict, Any
from data_parser import DataParser, DataValidator


class DatabaseLoader:
    """数据库加载器"""
    
    def __init__(self, db_path: str = 'insurance_data.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        self.connect()
        
        # 创建表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fulfillment_ratios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                product_name TEXT NOT NULL,
                product_type TEXT,
                category TEXT NOT NULL,
                currency TEXT NOT NULL,
                policy_year INTEGER,
                purchase_year INTEGER,
                fulfillment_rate INTEGER,
                status TEXT NOT NULL,
                data_year INTEGER NOT NULL,
                last_updated TEXT NOT NULL,
                data_source TEXT,
                UNIQUE(company, product_name, category, currency, policy_year, purchase_year, data_year)
            )
        ''')
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_company ON fulfillment_ratios(company)',
            'CREATE INDEX IF NOT EXISTS idx_product ON fulfillment_ratios(product_name)',
            'CREATE INDEX IF NOT EXISTS idx_currency ON fulfillment_ratios(currency)',
            'CREATE INDEX IF NOT EXISTS idx_year ON fulfillment_ratios(policy_year)',
            'CREATE INDEX IF NOT EXISTS idx_status ON fulfillment_ratios(status)',
        ]
        
        for index_sql in indexes:
            self.cursor.execute(index_sql)
        
        self.conn.commit()
        print("✅ 数据库表结构初始化完成")
    
    def clear_data(self, company: str = None):
        """清空数据"""
        self.connect()
        
        if company:
            self.cursor.execute('DELETE FROM fulfillment_ratios WHERE company = ?', (company,))
            print(f"✅ 已清空 {company} 的数据")
        else:
            self.cursor.execute('DELETE FROM fulfillment_ratios')
            print("✅ 已清空所有数据")
        
        self.conn.commit()
        self.close()
    
    def insert_records(self, records: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, int]:
        """批量插入记录"""
        self.connect()
        
        inserted = 0
        updated = 0
        skipped = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            for record in batch:
                try:
                    # 尝试插入
                    self.cursor.execute('''
                        INSERT INTO fulfillment_ratios 
                        (company, product_name, product_type, category, currency, 
                         policy_year, purchase_year, fulfillment_rate, status, data_year, 
                         last_updated, data_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record['company'],
                        record['product_name'],
                        record['product_type'],
                        record['category'],
                        record['currency'],
                        record['policy_year'],
                        record['purchase_year'],
                        record['fulfillment_rate'],
                        record['status'],
                        record['data_year'],
                        record['last_updated'],
                        record['data_source']
                    ))
                    inserted += 1
                    
                except sqlite3.IntegrityError:
                    # 记录已存在，尝试更新
                    self.cursor.execute('''
                        UPDATE fulfillment_ratios
                        SET fulfillment_rate = ?,
                            status = ?,
                            last_updated = ?,
                            data_source = ?
                        WHERE company = ? 
                          AND product_name = ? 
                          AND category = ? 
                          AND currency = ? 
                          AND policy_year = ? 
                          AND purchase_year = ?
                          AND data_year = ?
                    ''', (
                        record['fulfillment_rate'],
                        record['status'],
                        record['last_updated'],
                        record['data_source'],
                        record['company'],
                        record['product_name'],
                        record['category'],
                        record['currency'],
                        record['policy_year'],
                        record['purchase_year'],
                        record['data_year']
                    ))
                    
                    if self.cursor.rowcount > 0:
                        updated += 1
                    else:
                        skipped += 1
                
                except Exception as e:
                    print(f"❌ 插入记录失败: {e}")
                    print(f"   记录: {record}")
                    skipped += 1
            
            # 每批次提交一次
            self.conn.commit()
        
        self.close()
        
        return {
            'inserted': inserted,
            'updated': updated,
            'skipped': skipped,
            'total': len(records)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        self.connect()
        
        # 总记录数
        self.cursor.execute('SELECT COUNT(*) FROM fulfillment_ratios')
        total_records = self.cursor.fetchone()[0]
        
        # 按公司统计
        self.cursor.execute('''
            SELECT company, COUNT(*) as count 
            FROM fulfillment_ratios 
            GROUP BY company
        ''')
        by_company = dict(self.cursor.fetchall())
        
        # 按状态统计
        self.cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM fulfillment_ratios 
            GROUP BY status
        ''')
        by_status = dict(self.cursor.fetchall())
        
        # 按货币统计
        self.cursor.execute('''
            SELECT currency, COUNT(*) as count 
            FROM fulfillment_ratios 
            GROUP BY currency
        ''')
        by_currency = dict(self.cursor.fetchall())
        
        # 产品数量
        self.cursor.execute('''
            SELECT COUNT(DISTINCT product_name) 
            FROM fulfillment_ratios
        ''')
        total_products = self.cursor.fetchone()[0]
        
        self.close()
        
        return {
            'total_records': total_records,
            'total_products': total_products,
            'by_company': by_company,
            'by_status': by_status,
            'by_currency': by_currency
        }


def main():
    """主函数：执行完整的ETL流程"""
    print("="*60)
    print("香港保险分红实现率数据导入系统")
    print("="*60)
    
    # 1. 初始化数据库
    print("\n步骤 1: 初始化数据库")
    loader = DatabaseLoader('insurance_data.db')
    loader.init_database()
    
    # 2. 清空旧数据（可选）
    print("\n步骤 2: 清空旧数据")
    response = input("是否清空现有数据？(y/n): ")
    if response.lower() == 'y':
        loader.clear_data()
    
    # 3. 解析JSON数据
    print("\n步骤 3: 解析JSON数据")
    parser = DataParser(data_year=2024)
    
    print("  解析周大福数据...")
    ctf_records = parser.parse_ctf('/home/ubuntu/upload/pasted_file_WdsFng_extract-data-2026-02-12（ctf）.json')
    print(f"  ✅ 周大福: {len(ctf_records)} 条记录")
    
    print("  解析友邦数据...")
    aia_records = parser.parse_aia('/home/ubuntu/upload/pasted_file_liy7Iv_extract-data-2026-02-12(aia).json')
    print(f"  ✅ 友邦: {len(aia_records)} 条记录")
    
    print("  解析保诚数据...")
    pru_records = parser.parse_prudential('/home/ubuntu/upload/pasted_file_RiSJTW_extract-data-2026-02-12(prudential).json')
    print(f"  ✅ 保诚: {len(pru_records)} 条记录")
    
    all_records = ctf_records + aia_records + pru_records
    print(f"\n  总计: {len(all_records)} 条记录")
    
    # 4. 验证数据
    print("\n步骤 4: 验证数据质量")
    validation_result = DataValidator.validate_batch(all_records)
    print(f"  总记录数: {validation_result['total']}")
    print(f"  有效记录: {validation_result['valid']}")
    print(f"  无效记录: {validation_result['invalid']}")
    
    if validation_result['errors']:
        print(f"\n  ⚠️  发现 {len(validation_result['errors'])} 个错误:")
        for error in validation_result['errors'][:5]:  # 只显示前5个
            print(f"    - {error['product_name']}: {error['errors']}")
    
    # 5. 导入数据库
    print("\n步骤 5: 导入数据到数据库")
    # 过滤掉无效记录
    valid_records = [r for r in all_records if DataValidator.validate_record(r)[0]]
    
    result = loader.insert_records(valid_records)
    print(f"  ✅ 新增: {result['inserted']} 条")
    print(f"  ✅ 更新: {result['updated']} 条")
    print(f"  ⚠️  跳过: {result['skipped']} 条")
    
    # 6. 显示统计信息
    print("\n步骤 6: 数据库统计信息")
    stats = loader.get_statistics()
    print(f"  总记录数: {stats['total_records']}")
    print(f"  总产品数: {stats['total_products']}")
    
    print(f"\n  按公司分布:")
    for company, count in stats['by_company'].items():
        print(f"    - {company}: {count} 条")
    
    print(f"\n  按状态分布:")
    for status, count in stats['by_status'].items():
        print(f"    - {status}: {count} 条")
    
    print(f"\n  按货币分布:")
    for currency, count in stats['by_currency'].items():
        print(f"    - {currency}: {count} 条")
    
    print("\n" + "="*60)
    print("✅ 数据导入完成！")
    print("="*60)


if __name__ == '__main__':
    main()
