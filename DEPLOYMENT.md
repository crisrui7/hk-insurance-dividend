# 部署指南

## 🚀 快速部署到Streamlit Cloud

### 前置准备

1. ✅ GitHub账号
2. ✅ 项目代码已推送到GitHub仓库

### 详细步骤

#### 1. 准备GitHub仓库

```bash
# 初始化仓库（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit - HK Insurance Dividend Platform MVP"

# 连接到GitHub远程仓库
git remote add origin https://github.com/YOUR_USERNAME/hk-insurance-dividend.git

# 推送代码
git push -u origin main
```

#### 2. 确保项目文件完整

必需文件清单：
```
✅ app.py                    # Streamlit应用
✅ insurance_data.db         # 数据库文件
✅ requirements.txt          # Python依赖
✅ README.md                 # 项目说明
```

#### 3. 登录Streamlit Cloud

1. 访问 https://share.streamlit.io/
2. 点击右上角 "Sign in"
3. 使用GitHub账号登录授权

#### 4. 创建新应用

1. 点击 "New app" 按钮
2. 填写应用信息：
   - **Repository**: 选择你的仓库 `YOUR_USERNAME/hk-insurance-dividend`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (可选): 自定义子域名，如 `hk-insurance`

3. 点击 "Deploy!" 按钮

#### 5. 等待部署

- Streamlit会自动：
  1. 克隆你的仓库
  2. 安装 `requirements.txt` 中的依赖
  3. 运行 `app.py`
  
- 通常需要 2-5 分钟

#### 6. 访问应用

部署成功后，你会得到一个URL：
```
https://YOUR_APP_NAME.streamlit.app
```

或者你自定义的：
```
https://hk-insurance.streamlit.app
```

---

## 🔧 本地开发和测试

### 环境设置

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 生成数据

```bash
# 运行数据生成脚本
python create_sample_data.py

# 验证数据库已创建
ls -lh insurance_data.db
```

### 本地运行

```bash
# 启动Streamlit应用
streamlit run app.py

# 应用会在浏览器中自动打开
# 默认地址: http://localhost:8501
```

### 开发模式

Streamlit支持热重载，修改代码后：
1. 保存文件
2. 页面右上角会出现 "Source file changed" 提示
3. 点击 "Rerun" 或按 `R` 键重新加载

---

## 📊 数据更新流程

### 方案A: 手动更新（当前）

1. 修改 `create_sample_data.py` 中的数据
2. 运行脚本重新生成数据库
3. 提交并推送到GitHub
4. Streamlit Cloud自动重新部署

```bash
python create_sample_data.py
git add insurance_data.db
git commit -m "Update data - YYYY-MM-DD"
git push
```

### 方案B: 自动爬取（未来计划）

使用GitHub Actions定时任务：

`.github/workflows/update_data.yml`:
```yaml
name: Update Insurance Data

on:
  schedule:
    - cron: '0 0 1 * *'  # 每月1号运行
  workflow_dispatch:  # 允许手动触发

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run scraper
        run: python ctf_scraper.py
      
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add insurance_data.db
          git commit -m "Auto-update data" || exit 0
          git push
```

---

## 🌍 自定义域名（可选）

如果你有自己的域名，可以配置CNAME：

1. 在Streamlit Cloud应用设置中找到 "Custom domain"
2. 添加你的域名（如 `insurance.yourdomain.com`）
3. 在你的DNS服务商添加CNAME记录：
   ```
   Type: CNAME
   Name: insurance
   Value: YOUR_APP.streamlit.app
   ```

---

## 🐛 常见问题排查

### 问题1: 数据库文件找不到

**错误信息**:
```
sqlite3.OperationalError: unable to open database file
```

**解决方案**:
- 确保 `insurance_data.db` 已提交到Git
- 检查 `app.py` 中的数据库路径
- 使用相对路径而非绝对路径

### 问题2: 依赖安装失败

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement...
```

**解决方案**:
- 检查 `requirements.txt` 版本号是否正确
- 尝试移除版本号，使用最新版本
- 确保Python版本兼容（推荐3.9-3.12）

### 问题3: 应用启动缓慢

**原因**: Streamlit Cloud免费版资源有限

**解决方案**:
- 优化数据加载（使用 `@st.cache_resource`）
- 减少初始加载的数据量
- 考虑升级到付费版

### 问题4: 数据库更新后应用未刷新

**解决方案**:
1. 在Streamlit Cloud后台点击 "Reboot app"
2. 或修改 `app.py` 触发重新部署

---

## 📈 性能优化建议

### 1. 数据缓存

```python
@st.cache_resource
def load_data():
    # 数据加载逻辑
    pass
```

### 2. 延迟加载

只在用户需要时加载图表：
```python
with st.expander("查看详细图表"):
    # 图表渲染代码
    pass
```

### 3. 数据库优化

```sql
-- 创建索引加速查询
CREATE INDEX idx_product ON fulfillment_ratios(product_name);
CREATE INDEX idx_year ON fulfillment_ratios(policy_year);
```

---

## 🔐 安全考虑

### 生产环境建议

1. **API密钥管理**
   - 使用Streamlit Secrets管理敏感信息
   - 不要在代码中硬编码密钥

2. **访问控制**
   - 考虑添加简单的认证系统
   - 使用 `streamlit-authenticator` 库

3. **数据验证**
   - 验证用户输入
   - 防止SQL注入（使用参数化查询）

---

## 📞 技术支持

遇到问题？

1. 查看 [Streamlit官方文档](https://docs.streamlit.io/)
2. 访问 [Streamlit社区论坛](https://discuss.streamlit.io/)
3. 提交GitHub Issue

---

**最后更新**: 2026-02-06
