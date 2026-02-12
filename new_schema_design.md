# 数据表结构重构设计

## 一、当前结构（长格式）

### 现有表结构
```sql
CREATE TABLE fulfillment_ratios (
    id INTEGER PRIMARY KEY,
    company TEXT,
    product_name TEXT,
    category TEXT,              -- 週年紅利、歸原紅利、特別紅利等
    currency TEXT,
    policy_year INTEGER,
    fulfillment_rate INTEGER,
    status TEXT,
    data_year INTEGER,
    ...
);
```

### 问题
- 同一产品、同一购买年份的归原红利和特别红利分散在不同行
- 查询对比时需要JOIN或复杂的CASE WHEN
- 不直观，难以快速对比

### 示例数据（当前）
| product_name | category | policy_year | fulfillment_rate |
|--------------|----------|-------------|------------------|
| 理想人生 II | 歸原紅利 | 1 (2023) | 100 |
| 理想人生 II | 特別紅利 | 1 (2023) | 95 |
| 理想人生 II | 歸原紅利 | 2 (2022) | 98 |
| 理想人生 II | 特別紅利 | 2 (2022) | 93 |

---

## 二、新结构（宽格式）

### 新表结构
```sql
CREATE TABLE product_fulfillment_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 产品标识
    company TEXT NOT NULL,
    product_name TEXT NOT NULL,
    currency TEXT NOT NULL,
    
    -- 时间维度
    data_year INTEGER NOT NULL,          -- 报告年度（如2024）
    purchase_year INTEGER NOT NULL,      -- 购买年份（如2023、2022）
    policy_year INTEGER NOT NULL,        -- 保单年期（如1、2、3...）
    
    -- 分红实现率（宽格式）
    reversionary_bonus_rate INTEGER,     -- 歸原紅利实现率
    reversionary_bonus_status TEXT,      -- 歸原紅利状态
    
    special_bonus_rate INTEGER,          -- 特別紅利实现率
    special_bonus_status TEXT,           -- 特別紅利状态
    
    annual_bonus_rate INTEGER,           -- 週年紅利实现率
    annual_bonus_status TEXT,            -- 週年紅利状态
    
    terminal_bonus_rate INTEGER,         -- 終期紅利实现率
    terminal_bonus_status TEXT,          -- 終期紅利状态
    
    total_cash_value_rate INTEGER,      -- 總現金價值实现率
    total_cash_value_status TEXT,        -- 總現金價值状态
    
    -- 元数据
    last_updated TEXT NOT NULL,
    data_source TEXT,
    
    -- 唯一约束
    UNIQUE(company, product_name, currency, data_year, purchase_year)
);
```

### 优点
1. **直观对比**: 归原红利和特别红利在同一行，便于对比
2. **查询简单**: 无需JOIN，直接SELECT即可
3. **符合用户需求**: 按产品+购买年份索引，直接查看各类红利
4. **扩展性好**: 可以轻松添加其他红利类型

### 示例数据（新结构）
| product_name | purchase_year | reversionary_bonus_rate | special_bonus_rate |
|--------------|---------------|-------------------------|-------------------|
| 理想人生 II | 2023 | 100 | 95 |
| 理想人生 II | 2022 | 98 | 93 |
| 理想人生 II | 2021 | 96 | 91 |
| 理想人生 II | 2020 | NULL (N/A) | NULL (N/A) |

---

## 三、字段映射关系

### 分红类别映射
| 原category值 | 新字段名 | 英文说明 |
|-------------|---------|---------|
| 歸原紅利 | reversionary_bonus_rate | Reversionary Bonus |
| 特別紅利 | special_bonus_rate | Special Bonus |
| 週年紅利 | annual_bonus_rate | Annual Bonus |
| 終期紅利 | terminal_bonus_rate | Terminal Bonus |
| 總現金價值 | total_cash_value_rate | Total Cash Value |

### 购买年份提取
从 `policy_year` 字段提取：
- "1 (2023)" → purchase_year = 2023, policy_year = 1
- "2 (2022)" → purchase_year = 2022, policy_year = 2
- "10+ (2014 之前)" → purchase_year = 2014, policy_year = 10

---

## 四、索引设计

```sql
-- 主查询索引（按产品查询）
CREATE INDEX idx_product_lookup ON product_fulfillment_rates(
    company, product_name, currency, data_year
);

-- 按购买年份查询
CREATE INDEX idx_purchase_year ON product_fulfillment_rates(
    purchase_year
);

-- 按保单年期查询
CREATE INDEX idx_policy_year ON product_fulfillment_rates(
    policy_year
);

-- 组合索引（常用查询）
CREATE INDEX idx_company_product ON product_fulfillment_rates(
    company, product_name
);
```

---

## 五、数据转换逻辑

### 转换步骤
1. 从旧表读取数据，按 (company, product_name, currency, data_year, purchase_year) 分组
2. 使用PIVOT操作，将category转为列
3. 合并同一购买年份的不同分红类型到一行
4. 插入新表

### SQL示例
```sql
INSERT INTO product_fulfillment_rates (
    company, product_name, currency, data_year, purchase_year, policy_year,
    reversionary_bonus_rate, reversionary_bonus_status,
    special_bonus_rate, special_bonus_status,
    annual_bonus_rate, annual_bonus_status,
    last_updated
)
SELECT 
    company,
    product_name,
    currency,
    data_year,
    purchase_year,
    policy_year,
    MAX(CASE WHEN category = '歸原紅利' THEN fulfillment_rate END) as reversionary_bonus_rate,
    MAX(CASE WHEN category = '歸原紅利' THEN status END) as reversionary_bonus_status,
    MAX(CASE WHEN category = '特別紅利' THEN fulfillment_rate END) as special_bonus_rate,
    MAX(CASE WHEN category = '特別紅利' THEN status END) as special_bonus_status,
    MAX(CASE WHEN category = '週年紅利' THEN fulfillment_rate END) as annual_bonus_rate,
    MAX(CASE WHEN category = '週年紅利' THEN status END) as annual_bonus_status,
    MAX(last_updated) as last_updated
FROM fulfillment_ratios_with_purchase_year
GROUP BY company, product_name, currency, data_year, purchase_year, policy_year;
```

---

## 六、查询示例

### 查询某产品所有购买年份的红利对比
```sql
SELECT 
    purchase_year as 购买年份,
    reversionary_bonus_rate as 归原红利实现率,
    special_bonus_rate as 特别红利实现率
FROM product_fulfillment_rates
WHERE company = '保诚保险'
  AND product_name = '理想人生保障系列 II'
  AND currency = 'USD'
  AND data_year = 2024
ORDER BY purchase_year DESC;
```

### 查询2023年购买的所有产品
```sql
SELECT 
    product_name,
    reversionary_bonus_rate,
    special_bonus_rate
FROM product_fulfillment_rates
WHERE company = '保诚保险'
  AND purchase_year = 2023
  AND data_year = 2024;
```

---

## 七、兼容性考虑

### 保留旧表
- 旧表 `fulfillment_ratios` 保留作为备份
- 新表 `product_fulfillment_rates` 作为主查询表
- 前端应用更新为使用新表

### 迁移计划
1. 创建新表结构
2. 执行数据转换
3. 验证数据完整性
4. 更新前端应用
5. 测试所有功能
6. 备份旧表（可选：删除或重命名）

---

## 八、预期效果

### 数据量变化
- 旧表：3,886条记录
- 新表：约1,300-1,500条记录（合并后）
- 减少约60%的记录数

### 查询性能
- 查询速度提升：无需JOIN
- 代码简化：减少复杂的CASE WHEN
- 可读性提升：结果直观易懂

---

**设计版本**: v1.0  
**设计日期**: 2026-02-12  
**设计者**: Manus AI
