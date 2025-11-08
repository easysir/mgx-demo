# GitHub Issue 模板

## Feature 模板

```markdown
### 任务标题
[Feature] 任务简短描述

### 任务类型
- [ ] Feature (新功能)
- [ ] Bug (错误修复)
- [ ] Refactor (代码重构)
- [ ] Test (测试)
- [ ] Documentation (文档)

### 任务描述
详细描述任务的目标和背景。

### 验收标准
- [ ] 标准1：具体的可验证的标准
- [ ] 标准2：具体的可验证的标准
- [ ] 标准3：具体的可验证的标准

### 技术要点
- 关键技术点1
- 关键技术点2
- 关键技术点3

### 交付物
- [ ] 文件1：路径/文件名
- [ ] 文件2：路径/文件名
- [ ] 单元测试
- [ ] 文档更新

### 依赖任务
- 依赖任务1：#issue_number
- 依赖任务2：#issue_number

### 负责人
@username

### 预计工时
X 天

### Sprint
Sprint X (Week Y-Z)

### 优先级
- [ ] P0 (必须完成)
- [ ] P1 (应该完成)
- [ ] P2 (可以完成)

### 标签
`phase-1` `sprint-1` `backend` `frontend` `infrastructure`

### 备注
其他需要说明的信息。
```

---

## Bug 模板

```markdown
### Bug 标题
[Bug] Bug 简短描述

### Bug 类型
- [ ] 功能性 Bug
- [ ] 性能问题
- [ ] 安全问题
- [ ] UI/UX 问题

### 复现步骤
1. 步骤1
2. 步骤2
3. 步骤3

### 期望行为
描述期望的正确行为。

### 实际行为
描述实际发生的错误行为。

### 环境信息
- OS: [e.g. macOS 14.0]
- Browser: [e.g. Chrome 120]
- Backend Version: [e.g. v1.0.0]
- Frontend Version: [e.g. v1.0.0]

### 错误日志
```
粘贴相关的错误日志
```

### 截图
如果适用，添加截图帮助说明问题。

### 影响范围
- [ ] 阻塞性（无法继续开发）
- [ ] 严重（影响核心功能）
- [ ] 一般（影响部分功能）
- [ ] 轻微（不影响使用）

### 负责人
@username

### 优先级
- [ ] P0 (立即修复)
- [ ] P1 (本周修复)
- [ ] P2 (下周修复)

### 标签
`bug` `phase-1` `sprint-1` `backend` `frontend`
```

---

## Refactor 模板

```markdown
### 重构标题
[Refactor] 重构简短描述

### 重构原因
说明为什么需要重构，当前代码存在什么问题。

### 重构目标
- 目标1：提升性能
- 目标2：提高可维护性
- 目标3：减少技术债务

### 重构范围
- 文件1：路径/文件名
- 文件2：路径/文件名

### 重构方案
详细描述重构的具体方案和步骤。

### 风险评估
- 风险1：描述及应对策略
- 风险2：描述及应对策略

### 测试计划
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 性能测试通过

### 负责人
@username

### 预计工时
X 天

### 优先级
- [ ] P0 (必须完成)
- [ ] P1 (应该完成)
- [ ] P2 (可以完成)

### 标签
`refactor` `phase-1` `sprint-1` `backend` `frontend`
```

---

## Test 模板

```markdown
### 测试标题
[Test] 测试简短描述

### 测试类型
- [ ] 单元测试
- [ ] 集成测试
- [ ] E2E 测试
- [ ] 性能测试

### 测试范围
- 模块1：路径/文件名
- 模块2：路径/文件名

### 测试用例
1. 用例1：描述
   - 输入：xxx
   - 期望输出：xxx
2. 用例2：描述
   - 输入：xxx
   - 期望输出：xxx

### 覆盖率目标
- 单元测试：> 80%
- 集成测试：> 60%

### 负责人
@username

### 预计工时
X 天

### 优先级
- [ ] P0 (必须完成)
- [ ] P1 (应该完成)
- [ ] P2 (可以完成)

### 标签
`test` `phase-1` `sprint-1` `backend` `frontend`
```

---

## 使用说明

1. **创建 Issue**：根据任务类型选择对应的模板
2. **填写信息**：完整填写所有必填字段
3. **添加标签**：使用统一的标签体系
4. **关联任务**：在依赖任务中关联相关 Issue
5. **更新状态**：任务进行中及时更新状态和进度
6. **关闭 Issue**：完成后添加完成说明并关闭

## 标签体系

### Phase 标签
- `phase-1`: Phase 1 MVP 核心功能
- `phase-2`: Phase 2 功能扩展
- `phase-3`: Phase 3 高级功能

### Sprint 标签
- `sprint-1`: Sprint 1 (Week 1-2)
- `sprint-2`: Sprint 2 (Week 3-4)
- ...

### 模块标签
- `backend`: 后端相关
- `frontend`: 前端相关
- `infrastructure`: 基础设施
- `agent`: Agent 系统
- `database`: 数据库
- `api`: API 相关
- `websocket`: WebSocket 相关

### 优先级标签
- `priority-p0`: 必须完成
- `priority-p1`: 应该完成
- `priority-p2`: 可以完成

### 状态标签
- `status-todo`: 待开始
- `status-in-progress`: 进行中
- `status-review`: 代码审查中
- `status-blocked`: 被阻塞
- `status-done`: 已完成