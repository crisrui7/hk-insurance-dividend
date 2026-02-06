# 香港保险分红实现率查询平台 MVP

## 项目简介

这是一个用于查询和可视化香港各大保险公司分红实现率的Web应用。目前MVP版本专注于**周大福人寿**的数据。

### 核心功能

✅ **数据可视化**
- 分红实现率趋势图
- 多产品对比分析
- 按保单年期分布图
- 产品雷达图对比

✅ **灵活筛选**
- 按公司筛选
- 按产品筛选
- 按货币筛选（美元/港币/人民币）
- 按类别筛选（週年紅利/終期紅利/復歸紅利等）
- 按保单年期范围筛选

✅ **详细数据**
- 完整数据表格展示
- 状态标识（正常/已停售/未推出等）
- CSV数据导出功能

## 技术栈

- **后端**: Python 3.12
- **数据库**: SQLite
- **前端框架**: Streamlit
- **数据处理**: Pandas
- **可视化**: Plotly
- **爬虫**: BeautifulSoup4, Requests

## 项目结构

```
├── app.py                      # Streamlit主应用
├── create_sample_data.py       # 样本数据生成器
├── ctf_scraper.py             # 周大福爬虫（在线版）
├── ctf_parser.py              # 数据解析器（离线版）
├── insurance_data.db          # SQLite数据库
├── ctf_sample_data.csv        # CSV导出数据
├── requirements.txt           # Python依赖
└── README.md                  # 项目文档
```

## 数据结构

### 数据库Schema

**fulfillment_ratios** 表：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| company | TEXT | 保险公司名称 |
| product_name | TEXT | 产品名称 |
| product_type | TEXT | 产品类型 |
| category | TEXT | 类别（週年紅利/終期紅利等） |
| currency | TEXT | 货币 |
| policy_year | INTEGER | 保单年期 |
| fulfillment_rate | INTEGER | 分红实现率(%) |
| status | TEXT | 状态标识 |
| data_year | INTEGER | 数据年度 |
| last_updated | TEXT | 最后更新日期 |

### 状态码说明

| 状态码 | 中文 | 含义 |
|--------|------|------|
| normal | 正常 | 有实际分红实现率数据 |
| discontinued | 已停售 | 产品已停售 |
| not_launched | 未推出 | 该年期尚未推出 |
| no_dividend | 無分紅 | 该年期无分红 |
| no_termination | 無保單終結 | 无保单终结 |
| not_reached_yet | 未達保單年期 | 未达到该保单年期 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 生成样本数据

```bash
python create_sample_data.py
```

这将创建：
- `insurance_data.db` - SQLite数据库
- `ctf_sample_data.csv` - CSV数据文件

### 3. 运行应用

```bash
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动

## 部署到Streamlit Cloud

### 步骤：

1. **准备GitHub仓库**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **登录Streamlit Cloud**
   - 访问 https://share.streamlit.io/
   - 使用GitHub账号登录

3. **创建新应用**
   - 点击 "New app"
   - 选择你的GitHub仓库
   - 主文件路径：`app.py`
   - 点击 "Deploy"

4. **等待部署完成**
   - Streamlit会自动安装依赖
   - 几分钟后应用即可访问

## 数据更新策略

### 当前（MVP阶段）
- 使用静态样本数据
- 手动更新数据库

### 未来计划
1. **自动化爬虫**
   - 定期（每月）自动爬取官网数据
   - 使用GitHub Actions定时任务
   
2. **数据验证**
   - 自动检测数据变化
   - 异常值提醒
   
3. **历史数据**
   - 存储历史版本
   - 趋势对比分析

## 扩展路线图

### 阶段2: 添加更多保险公司
- [ ] 保诚 (Prudential)
- [ ] 友邦 (AIA)
- [ ] 宏利 (Manulife)
- [ ] 安盛 (AXA)

### 阶段3: 高级功能
- [ ] 用户账户系统
- [ ] 产品收藏功能
- [ ] 数据对比报告生成
- [ ] 邮件订阅更新提醒
- [ ] 移动端优化

### 阶段4: 数据分析
- [ ] AI预测分红趋势
- [ ] 产品推荐系统
- [ ] 风险评估工具

## 使用截图

（部署后添加实际截图）

### 主界面
- 关键指标概览
- 筛选器面板

### 趋势图表
- 分红实现率折线图
- 按年期柱状图

### 产品对比
- 多产品雷达图
- 对比分析表

## 注意事项

⚠️ **免责声明**

1. 本平台数据仅供参考，不构成投资建议
2. 过往表现不代表未来结果
3. 实际分红以保险公司公告为准
4. 投资有风险，决策需谨慎

## 数据来源

- 周大福人寿官网：https://www.ctflife.com.hk/tc/support/important-information/fulfillment-ratios-dividends

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 开发者

- 初始开发：[Your Name]
- 联系方式：[Your Email]

## 许可证

MIT License

## 更新日志

### v0.1.0 (2026-02-06) - MVP版本
- ✅ 完成周大福人寿数据结构
- ✅ 实现基础可视化功能
- ✅ 支持多维度筛选
- ✅ 产品对比分析
- ✅ CSV导出功能

---

**最后更新**: 2026-02-06
