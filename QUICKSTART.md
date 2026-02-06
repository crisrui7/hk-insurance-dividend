# ⚡ 快速启动指南

## 5分钟部署到云端

### 步骤1: 准备GitHub (2分钟)

```bash
# 1. 创建新仓库（在GitHub网站上）
# 仓库名: hk-insurance-dividend

# 2. 克隆到本地
git clone https://github.com/YOUR_USERNAME/hk-insurance-dividend.git
cd hk-insurance-dividend

# 3. 复制项目文件到仓库目录
# 将下载的所有文件复制到这个目录

# 4. 提交并推送
git add .
git commit -m "Initial commit - MVP"
git push origin main
```

### 步骤2: 部署到Streamlit Cloud (3分钟)

1. 访问 https://share.streamlit.io/
2. 使用GitHub登录
3. 点击 "New app"
4. 选择:
   - Repository: `YOUR_USERNAME/hk-insurance-dividend`
   - Branch: `main`
   - Main file: `app.py`
5. 点击 "Deploy!"
6. 等待2-3分钟

完成！🎉

你的应用地址: `https://YOUR-APP.streamlit.app`

---

## 本地运行（开发）

### 方法1: 最简单

```bash
# 安装依赖
pip install streamlit pandas plotly

# 运行应用
streamlit run app.py
```

访问: http://localhost:8501

### 方法2: 使用虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

## 常用命令

### 数据更新

```bash
# 重新生成样本数据
python create_sample_data.py

# 查看数据
sqlite3 insurance_data.db "SELECT * FROM fulfillment_ratios LIMIT 10;"
```

### Git操作

```bash
# 更新数据后推送
git add insurance_data.db
git commit -m "Update data"
git push

# Streamlit会自动重新部署
```

### 调试

```bash
# 查看Streamlit版本
streamlit --version

# 清除缓存
streamlit cache clear

# 详细日志
streamlit run app.py --logger.level=debug
```

---

## 问题排查

### ❌ ModuleNotFoundError: No module named 'streamlit'

```bash
pip install streamlit
```

### ❌ 数据库找不到

确保 `insurance_data.db` 在项目根目录

### ❌ 端口被占用

```bash
# 使用其他端口
streamlit run app.py --server.port 8502
```

### ❌ 部署后数据不显示

检查GitHub仓库是否包含 `insurance_data.db`

---

## 快速测试清单

- [ ] 页面正常加载
- [ ] 所有筛选器可用
- [ ] 图表正常显示
- [ ] 数据表格显示正确
- [ ] CSV导出功能正常
- [ ] 产品对比功能正常

全部通过？恭喜！✅

---

## 下一步建议

### 立即：
1. 分享给朋友测试
2. 收集反馈
3. 记录问题

### 本周：
1. 美化UI
2. 添加更多产品数据
3. 优化性能

### 本月：
1. 开发爬虫
2. 添加新公司
3. 增加高级功能

---

## 获取帮助

- 📖 查看 `README.md` - 完整文档
- 🚀 查看 `DEPLOYMENT.md` - 详细部署指南
- 📊 查看 `PROJECT_SUMMARY.md` - 项目总结

需要帮助？提交GitHub Issue！

---

**祝你成功！🚀**
