# ValueGraph Git 工作流规范

**版本**: v1.0  
**创建日期**: 2026-03-22 22:30  
**GitHub 仓库**: https://github.com/yi5an/valuegraph.git

---

## 🌿 分支策略

### 主要分支
- **main**: 生产分支（稳定版本）
- **develop**: 开发分支（集成测试）
- **feature/week-N**: 功能分支（每周开发）

### 分支命名规范
```
feature/week-1-project-init      # Week 1: 项目初始化
feature/week-2-3-value-screening # Week 2-3: 价值筛选
feature/week-4-financial-data    # Week 4: 财报数据
feature/week-5-visualization     # Week 5: 时间线可视化
feature/week-6-shareholders      # Week 6: 持股查询
feature/week-7-testing           # Week 7: 集成测试
feature/week-8-deployment        # Week 8: 部署上线
```

---

## 📋 工作流程

### 1. 新阶段开发前
```bash
# 从 main 创建新分支
git checkout main
git pull origin main
git checkout -b feature/week-N-description

# 推送到远程
git push -u origin feature/week-N-description
```

### 2. 开发过程中
```bash
# 每天提交代码
git add .
git commit -m "feat: 描述"

# 推送到远程
git push origin feature/week-N-description
```

### 3. 阶段完成后
```bash
# 1. 确保所有代码已提交
git add .
git commit -m "feat(week-N): 完成阶段功能"

# 2. 推送到远程
git push origin feature/week-N-description

# 3. 等待测试通过
# @tester 验证功能

# 4. 测试通过后合并到 main
git checkout main
git pull origin main
git merge feature/week-N-description
git push origin main

# 5. 创建 tag
git tag -a v0.N.0 -m "Week N 完成"
git push origin v0.N.0

# 6. 删除功能分支（可选）
git branch -d feature/week-N-description
git push origin --delete feature/week-N-description
```

---

## 📝 Commit 规范

### 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型
- **feat**: 新功能
- **fix**: Bug 修复
- **docs**: 文档更新
- **style**: 代码格式（不影响功能）
- **refactor**: 重构
- **test**: 测试相关
- **chore**: 构建/工具相关

### 示例
```bash
# 新功能
git commit -m "feat(week-2): 实现价值筛选算法"

# Bug 修复
git commit -m "fix(api): 修复 NaN 序列化错误"

# 文档更新
git commit -m "docs(api): 更新 API 接口文档"

# 测试
git commit -m "test(week-2): 添加价值筛选单元测试"
```

---

## 🏷️ Tag 规范

### 版本号
- **v0.1.0**: Week 1-3 完成（MVP 核心功能）
- **v0.2.0**: Week 4-5 完成（财报深度分析）
- **v0.3.0**: Week 6 完成（持股信息查询）
- **v1.0.0**: Week 7-8 完成（生产环境上线）

### Tag 格式
```bash
git tag -a v0.1.0 -m "Week 1-3: MVP 核心功能完成

功能列表：
- 项目初始化
- 数据源集成（AkShare + Tushare）
- 价值筛选算法
- 前端基础页面
- API 接口

测试状态：✅ 通过
文档状态：✅ 完成
"
```

---

## 🔐 敏感信息保护

### 不要提交的文件
```gitignore
# .gitignore
.env
.env.local
*.key
*.pem
secrets/
credentials/
```

### 环境变量处理
```bash
# 使用 .env.example 作为模板
cp .env.example .env
# 编辑 .env 填入真实值
```

---

## 📊 阶段验收清单

### 每个阶段完成后检查
- [ ] 代码已提交到功能分支
- [ ] @tester 测试通过
- [ ] @documenter 文档完成
- [ ] 代码已合并到 main
- [ ] Tag 已创建
- [ ] GitHub Release 已发布

---

## 🔄 当前状态

### Week 2-3（价值筛选功能）
- **分支**: feature/week-2-3-value-screening
- **状态**: 🔄 开发完成，测试失败，修复中
- **待办**:
  1. ✅ 修复 P0 问题
  2. ⏸️ 测试通过
  3. ⏸️ 合并到 main
  4. ⏸️ 创建 tag v0.1.0

### Week 4（财报数据完善）
- **分支**: feature/week-4-financial-data
- **状态**: ⏸️ 等待 Week 2-3 完成后开始

---

## 📅 下一步行动

### 立即行动（今晚）
1. 初始化 Git 仓库
2. 提交 Week 2-3 代码到 feature/week-2-3-value-screening
3. 等待修复完成
4. 测试通过后合并到 main
5. 创建 tag v0.1.0

### 明天开始（Week 4）
1. 从 main 创建 feature/week-4-financial-data
2. 开始财报数据完善开发

---

**更新时间**: 2026-03-22 22:30
