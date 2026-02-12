# 数据结构分析报告

## 一、JSON数据结构对比

### 1. 周大福（CTF）
- **记录数量**: 383条
- **数据结构**: 扁平化结构，每条记录包含完整信息
- **关键字段**:
  - `product_name`: 产品名称
  - `currency`: 货币（USD/HKD/RMB）
  - `report_year`: 报告年度（2024）
  - `policy_year`: 保单年期（数字）
  - `ratio`: 分红实现率（小数，1表示100%）
  - `type`: 类型（Dividend/Terminal Bonus等）

**优点**: 数据结构清晰，易于处理
**缺点**: 包含大量citation字段（可能是爬虫工具自动添加的）

### 2. 友邦（AIA）
- **记录数量**: 1573条（分为两个类别）
- **数据结构**: 扁平化结构，但字段命名不同
- **关键字段**:
  - `product_name`: 产品名称（中文）
  - `currency`: 货币（"所有"表示通用）
  - `policy_year`: 保单年期（字符串格式："第X個保單年度 (YYYY)"）
  - `fulfillment_ratio`: 分红实现率（字符串，如"84%"或"Closed to sales"）

**优点**: 数据量大，信息丰富
**缺点**: 
- `policy_year`是字符串，需要解析
- `fulfillment_ratio`包含非数字状态值
- 产品名称是中文，需要标准化

### 3. 保诚（Prudential）
- **记录数量**: 208条产品
- **数据结构**: 嵌套结构，每个产品包含多个年期的数据
- **关键字段**:
  - `product_name`: 产品名称（包含货币和类型信息）
  - `fulfillment_ratios`: 数组，包含多个年期的数据
    - `policy_year`: 保单年期（字符串："X (YYYY)"）
    - `percentage`: 分红实现率（字符串，如"16%"或"N/A(1)"）

**优点**: 数据组织合理，按产品分组
**缺点**: 
- 嵌套结构需要展开处理
- 产品名称包含多个信息维度，需要拆分
- 百分比格式不统一

## 二、数据清洗需求

### 1. 字段标准化
| 原始字段 | 标准字段 | 说明 |
|---------|---------|------|
| CTF: ratio | fulfillment_rate | 统一为百分比整数 |
| AIA: fulfillment_ratio | fulfillment_rate | 需要解析百分比 |
| Prudential: percentage | fulfillment_rate | 需要解析百分比 |
| CTF: type | category | 分红类别 |
| AIA: policy_year | policy_year | 需要提取年份数字 |
| Prudential: policy_year | policy_year | 需要提取年份数字 |

### 2. 状态码映射
需要将各种非数字状态统一映射到标准状态码：

| 原始值 | 标准状态码 | 中文说明 |
|-------|-----------|---------|
| "Closed to sales" | discontinued | 已停售 |
| "N/A(1)" | not_launched | 未推出 |
| "N/A" | no_data | 无数据 |
| 数字值 | normal | 正常 |

### 3. 产品名称处理
- **保诚**: 需要从产品名称中提取货币和分红类型
  - 示例: "「理想人生」保障系列 II - 分期繳費 (美元) [2024 報告年度的歸原紅利現金價值分紅實現率]"
  - 提取: 产品名="「理想人生」保障系列 II", 货币="美元", 类别="歸原紅利"

- **友邦**: 产品名称较规范，但需要去除多余空格

- **周大福**: 产品名称包含状态标识"(Closed to sales)"，需要提取

## 三、爬虫方案评估

### Firecrawl方案分析

**优点**:
1. ✅ 成功提取了结构化数据
2. ✅ 自动添加citation字段，便于追溯数据来源
3. ✅ 能处理复杂的网页结构
4. ✅ 无需编写复杂的解析代码

**缺点**:
1. ❌ 数据格式不统一（三家公司结构差异大）
2. ❌ 包含大量冗余字段（citation字段）
3. ❌ 可能有成本考虑（如果是付费服务）
4. ❌ 依赖外部服务，不易调试和定制

### 替代方案建议

#### 方案A: BeautifulSoup + Requests（推荐）
**适用场景**: 静态HTML页面

**优点**:
- 完全免费
- 完全可控，易于调试
- 可以自定义数据格式
- 轻量级，依赖少

**缺点**:
- 需要为每个保司编写解析器
- 网页结构变化时需要更新代码

**实现难度**: ⭐⭐⭐ (中等)

#### 方案B: Selenium + BeautifulSoup
**适用场景**: 动态加载的JavaScript页面

**优点**:
- 能处理动态内容
- 可以模拟用户操作
- 适合复杂交互场景

**缺点**:
- 较重，需要浏览器驱动
- 速度较慢
- 资源消耗大

**实现难度**: ⭐⭐⭐⭐ (较难)

#### 方案C: Scrapy框架
**适用场景**: 大规模爬取，多个网站

**优点**:
- 高性能，支持并发
- 内置数据管道
- 适合长期维护

**缺点**:
- 学习曲线陡峭
- 对于3个网站来说过于重量级

**实现难度**: ⭐⭐⭐⭐⭐ (困难)

#### 方案D: 继续使用Firecrawl + 数据清洗层
**适用场景**: 快速迭代，不想维护爬虫代码

**优点**:
- 保持现有工作流
- 专注于数据处理和展示
- 减少维护成本

**缺点**:
- 可能有持续成本
- 数据格式依赖外部服务

**实现难度**: ⭐⭐ (简单)

## 四、推荐方案

### 短期方案（MVP阶段）
**继续使用Firecrawl + 构建统一的数据清洗层**

理由:
1. 您已经有了可用的数据
2. 可以快速验证产品价值
3. 专注于前端展示和用户体验
4. 数据清洗层可以标准化不同来源的数据

### 中期方案（产品验证后）
**迁移到BeautifulSoup自建爬虫**

理由:
1. 降低长期成本
2. 完全可控，易于定制
3. 可以实现自动化定时更新
4. 三个保司的网站都是静态HTML，技术难度不高

### 长期方案（规模化后）
**构建完整的数据采集平台**

包括:
1. 爬虫调度系统（Airflow/Celery）
2. 数据验证和质量监控
3. 历史数据版本管理
4. 异常告警机制

## 五、数据库设计建议

### 当前数据库问题
查看现有的`insurance_data.db`，发现只有周大福的样本数据。

### 改进建议

#### 1. 保持现有Schema，但扩展字段
```sql
CREATE TABLE fulfillment_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,              -- 公司名称
    product_name TEXT NOT NULL,         -- 产品名称
    product_type TEXT,                  -- 产品类型
    category TEXT NOT NULL,             -- 分红类别
    currency TEXT NOT NULL,             -- 货币
    policy_year INTEGER NOT NULL,       -- 保单年期
    fulfillment_rate INTEGER,           -- 分红实现率(%)
    status TEXT NOT NULL,               -- 状态码
    data_year INTEGER NOT NULL,         -- 数据年度
    last_updated TEXT NOT NULL,         -- 最后更新时间
    data_source TEXT,                   -- 数据来源URL
    UNIQUE(company, product_name, category, currency, policy_year, data_year)
);
```

#### 2. 添加索引
```sql
CREATE INDEX idx_company ON fulfillment_ratios(company);
CREATE INDEX idx_product ON fulfillment_ratios(product_name);
CREATE INDEX idx_currency ON fulfillment_ratios(currency);
CREATE INDEX idx_year ON fulfillment_ratios(policy_year);
```

#### 3. 考虑添加产品表（可选）
如果需要存储更多产品元数据：
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    product_name TEXT NOT NULL,
    product_name_en TEXT,
    product_type TEXT,
    launch_date TEXT,
    discontinued_date TEXT,
    description TEXT,
    UNIQUE(company, product_name)
);
```

## 六、ETL流程设计

```
JSON文件 → 数据解析器 → 数据清洗 → 数据验证 → 数据库存储
   ↓           ↓            ↓           ↓           ↓
 CTF.json   统一格式    标准化字段   质量检查    SQLite
 AIA.json   
 PRU.json   
```

### 关键步骤:
1. **解析器**: 为每个保司编写专门的解析器
2. **清洗器**: 统一字段格式和数据类型
3. **验证器**: 检查数据完整性和合理性
4. **加载器**: 批量插入或更新数据库

## 七、下一步行动建议

1. ✅ 实现统一的数据解析和清洗模块
2. ✅ 将三家保司的JSON数据导入数据库
3. ✅ 更新前端应用，支持多公司筛选
4. ⏳ 编写数据质量报告
5. ⏳ 部署更新到Streamlit Cloud
6. ⏳ （可选）开始编写BeautifulSoup爬虫替代Firecrawl
