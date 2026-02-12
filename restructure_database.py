#!/usr/bin/env python3
"""
数据库结构重构脚本
将长格式（category作为行）转换为宽格式（category作为列）
"""

import sqlite3
import re
from datetime import datetime

class DatabaseRestructurer:
    """数据库重构器"""
    
    def __init__(self, db_path='insurance_data.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            
    def extract_purchase_year(self, policy_year_str):
        """
        从policy_year字段提取购买年份
        例如: "1 (2023)" -> 2023
              "10+ (2014 之前)" -> 2014
        """
        if not policy_year_str:
            return None
            
        # 提取括号中的年份
        match = re.search(r'\((\d{4})', str(policy_year_str))
        if match:
            return int(match.group(1))
        
        return None
    
    def create_new_table(self):
        """创建新表结构"""
        print("创建新表 product_fulfillment_rates...")
        
        cursor = self.conn.cursor()
        
        # 删除旧表（如果存在）
        cursor.execute("DROP TABLE IF EXISTS product_fulfillment_rates")
        
        # 创建新表
        cursor.execute("""
        CREATE TABLE product_fulfillment_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- 产品标识
            company TEXT NOT NULL,
            product_name TEXT NOT NULL,
            product_type TEXT,
            currency TEXT NOT NULL,
            
            -- 时间维度
            data_year INTEGER NOT NULL,
            purchase_year INTEGER NOT NULL,
            policy_year INTEGER,  -- 允许NULL，因为周大福数据没有policy_year
            
            -- 分红实现率（宽格式）
            reversionary_bonus_rate INTEGER,
            reversionary_bonus_status TEXT,
            
            special_bonus_rate INTEGER,
            special_bonus_status TEXT,
            
            annual_bonus_rate INTEGER,
            annual_bonus_status TEXT,
            
            terminal_bonus_rate INTEGER,
            terminal_bonus_status TEXT,
            
            total_cash_value_rate INTEGER,
            total_cash_value_status TEXT,
            
            -- 元数据
            last_updated TEXT NOT NULL,
            data_source TEXT,
            
            -- 唯一约束
            UNIQUE(company, product_name, currency, data_year, purchase_year)
        )
        """)
        
        # 创建索引
        cursor.execute("""
        CREATE INDEX idx_product_lookup ON product_fulfillment_rates(
            company, product_name, currency, data_year
        )
        """)
        
        cursor.execute("""
        CREATE INDEX idx_purchase_year ON product_fulfillment_rates(purchase_year)
        """)
        
        cursor.execute("""
        CREATE INDEX idx_policy_year ON product_fulfillment_rates(policy_year)
        """)
        
        cursor.execute("""
        CREATE INDEX idx_company_product ON product_fulfillment_rates(company, product_name)
        """)
        
        self.conn.commit()
        print("✓ 新表创建成功")
        
    def transform_data(self):
        """转换数据"""
        print("\n开始数据转换...")
        
        cursor = self.conn.cursor()
        
        # 1. 先创建临时表，添加purchase_year字段
        print("  - 创建临时表...")
        cursor.execute("""
        CREATE TEMPORARY TABLE temp_with_purchase_year AS
        SELECT 
            *,
            CAST(
                CASE 
                    WHEN policy_year LIKE '%(%' THEN 
                        SUBSTR(policy_year, INSTR(policy_year, '(') + 1, 4)
                    ELSE NULL
                END AS INTEGER
            ) as purchase_year
        FROM fulfillment_ratios
        """)
        
        # 2. 使用PIVOT转换数据
        print("  - 执行PIVOT转换...")
        cursor.execute("""
        INSERT INTO product_fulfillment_rates (
            company, product_name, product_type, currency, 
            data_year, purchase_year, policy_year,
            reversionary_bonus_rate, reversionary_bonus_status,
            special_bonus_rate, special_bonus_status,
            annual_bonus_rate, annual_bonus_status,
            terminal_bonus_rate, terminal_bonus_status,
            total_cash_value_rate, total_cash_value_status,
            last_updated, data_source
        )
        SELECT 
            company,
            product_name,
            MAX(product_type) as product_type,
            currency,
            data_year,
            purchase_year,
            MIN(policy_year) as policy_year,  -- 使用最小的policy_year作为代表
            
            -- 歸原紅利
            MAX(CASE WHEN category = '歸原紅利' THEN fulfillment_rate END) as reversionary_bonus_rate,
            MAX(CASE WHEN category = '歸原紅利' THEN status END) as reversionary_bonus_status,
            
            -- 特別紅利
            MAX(CASE WHEN category = '特別紅利' THEN fulfillment_rate END) as special_bonus_rate,
            MAX(CASE WHEN category = '特別紅利' THEN status END) as special_bonus_status,
            
            -- 週年紅利
            MAX(CASE WHEN category = '週年紅利' THEN fulfillment_rate END) as annual_bonus_rate,
            MAX(CASE WHEN category = '週年紅利' THEN status END) as annual_bonus_status,
            
            -- 終期紅利
            MAX(CASE WHEN category = '終期紅利' THEN fulfillment_rate END) as terminal_bonus_rate,
            MAX(CASE WHEN category = '終期紅利' THEN status END) as terminal_bonus_status,
            
            -- 總現金價值 / Total Value
            MAX(CASE WHEN category IN ('總現金價值', 'Total Value') THEN fulfillment_rate END) as total_cash_value_rate,
            MAX(CASE WHEN category IN ('總現金價值', 'Total Value') THEN status END) as total_cash_value_status,
            
            MAX(last_updated) as last_updated,
            MAX(data_source) as data_source
        FROM temp_with_purchase_year
        WHERE purchase_year IS NOT NULL  -- 只处理有购买年份的记录
        GROUP BY company, product_name, currency, data_year, purchase_year
        """)
        
        self.conn.commit()
        
        # 获取转换后的记录数
        cursor.execute("SELECT COUNT(*) FROM product_fulfillment_rates")
        new_count = cursor.fetchone()[0]
        
        print(f"✓ 数据转换完成，共 {new_count} 条记录")
        
        return new_count
    
    def validate_data(self):
        """验证数据完整性"""
        print("\n验证数据完整性...")
        
        cursor = self.conn.cursor()
        
        # 1. 统计各公司记录数
        print("\n【各公司记录数】")
        cursor.execute("""
        SELECT company, COUNT(*) as count
        FROM product_fulfillment_rates
        GROUP BY company
        ORDER BY count DESC
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} 条")
        
        # 2. 统计有数据的记录
        print("\n【有效数据统计】")
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN reversionary_bonus_rate IS NOT NULL THEN 1 ELSE 0 END) as has_reversionary,
            SUM(CASE WHEN special_bonus_rate IS NOT NULL THEN 1 ELSE 0 END) as has_special,
            SUM(CASE WHEN annual_bonus_rate IS NOT NULL THEN 1 ELSE 0 END) as has_annual,
            SUM(CASE WHEN terminal_bonus_rate IS NOT NULL THEN 1 ELSE 0 END) as has_terminal,
            SUM(CASE WHEN total_cash_value_rate IS NOT NULL THEN 1 ELSE 0 END) as has_total_value
        FROM product_fulfillment_rates
        """)
        row = cursor.fetchone()
        print(f"  总记录数: {row[0]}")
        print(f"  有归原红利: {row[1]} ({row[1]*100/row[0]:.1f}%)")
        print(f"  有特别红利: {row[2]} ({row[2]*100/row[0]:.1f}%)")
        print(f"  有周年红利: {row[3]} ({row[3]*100/row[0]:.1f}%)")
        print(f"  有终期红利: {row[4]} ({row[4]*100/row[0]:.1f}%)")
        print(f"  有总现金价值: {row[5]} ({row[5]*100/row[0]:.1f}%)")
        
        # 3. 查看保诚的示例数据
        print("\n【保诚保险示例数据】")
        cursor.execute("""
        SELECT 
            product_name,
            purchase_year,
            reversionary_bonus_rate,
            special_bonus_rate
        FROM product_fulfillment_rates
        WHERE company = '保诚保险'
          AND (reversionary_bonus_rate IS NOT NULL OR special_bonus_rate IS NOT NULL)
        ORDER BY product_name, purchase_year DESC
        LIMIT 5
        """)
        print(f"  {'产品名称':<30} {'购买年份':<10} {'归原红利':<10} {'特别红利':<10}")
        print("  " + "-" * 70)
        for row in cursor.fetchall():
            rev = row[2] if row[2] else 'N/A'
            spe = row[3] if row[3] else 'N/A'
            print(f"  {row[0]:<30} {row[1]:<10} {str(rev):<10} {str(spe):<10}")
        
        print("\n✓ 数据验证完成")
    
    def backup_old_table(self):
        """备份旧表"""
        print("\n备份旧表...")
        cursor = self.conn.cursor()
        
        # 重命名旧表
        cursor.execute("ALTER TABLE fulfillment_ratios RENAME TO fulfillment_ratios_backup")
        
        self.conn.commit()
        print("✓ 旧表已重命名为 fulfillment_ratios_backup")
    
    def run(self, backup_old=True):
        """执行完整的重构流程"""
        try:
            self.connect()
            
            print("="*80)
            print("数据库结构重构")
            print("="*80)
            
            # 1. 创建新表
            self.create_new_table()
            
            # 2. 转换数据
            new_count = self.transform_data()
            
            # 3. 验证数据
            self.validate_data()
            
            # 4. 备份旧表（可选）
            if backup_old:
                self.backup_old_table()
            
            print("\n" + "="*80)
            print("✓ 数据库重构完成！")
            print("="*80)
            print(f"\n新表: product_fulfillment_rates ({new_count} 条记录)")
            if backup_old:
                print("旧表: fulfillment_ratios_backup (已备份)")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            if self.conn:
                self.conn.rollback()
        finally:
            self.close()


def main():
    """主函数"""
    restructurer = DatabaseRestructurer('insurance_data.db')
    restructurer.run(backup_old=True)


if __name__ == '__main__':
    main()
