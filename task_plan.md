# Task Plan: Stage 2B-1 实机验收 checkpoint

## Goal
为现有 GitHub repository 添加 origin，核对本地 master 与远端默认/main 历史和 Stage 1 runtime 完整性，仅在可证明安全时将 Stage 2B-1 整合到远端主分支；绝不 force push、删除分支或进入 Koyeb/Stage 2B-2。

## Current Phase
Stage 2B-1 COMPLETED / VERIFIED；记录实机验收并创建文档 checkpoint。Stage 2B-2 尚未开始。

## Real-device Acceptance Checkpoint (2026-09-01)

- [x] Nook Simple Touch BNRV300 + Phoenix Phase 4 / FW 1.2.2 实机通过
- [x] TRMNL Nook Client v0.16.0 Self-Hosted / BYOS 最小闭环通过
- [x] Render Free Web Service（Singapore）公网 `/health`、`/api/display`、`/screen/test.png` 通过
- [x] 手机热点访问、认证、PNG 下载和显示通过
- [x] 800×600 预旋转图经客户端旋转后正确显示为 600×800 竖屏
- [x] 四角方向、双边框、无明显裁切及中文显示通过
- [x] 当前刷新测试值记录为 300 秒
- [ ] 校园网 PEAP 验证
- [ ] Render Free 冷启动与长期运行验证
- [ ] Stage 2B-2（未开始）

**Status:** complete — 本轮仅更新项目记录并 checkpoint，不修改服务端、网页、Nook 或 Render 配置。

## Verified Baselines
- Stage 1A–1C 均已由用户真实验收。
- Stage 1C-B checkpoint：`becdc39 chore: checkpoint verified stage 1C-B`
- Nook BNRV300：Phoenix Phase 4 / FW 1.2.2，TRMNL Nook client v0.16.0 已安装。

## Phases

### Phase 1: 协议、现状与部署资料核对
- [x] session catchup、完整需求和工作树检查
- [x] 建立 Stage 1C-B checkpoint
- [x] 读取 v0.16.0 实际客户端源码
- [x] 确认 headers、JSON、URL 拼接、filename、refresh_rate、图像尺寸/方向
- [x] 核对 2–3 个轻量 Python HTTPS 部署选项
- **Status:** complete

### Phase 2: 设计与规划记录
- [x] 确定最小 server 目录和配置边界
- [x] 确定 device ID/API key 校验与公开图片访问方案
- [x] 确定测试图尺寸与生成方式
- [x] 更新 findings/progress
- **Status:** complete

### Phase 3: 实现
- [x] 新增 FastAPI app、requirements、env example、gitignore
- [x] 实现 `/health`、`/api/display`、`/screen/test.png`
- [x] 生成有方向标记的固定测试图
- [x] 添加轻量自动测试和 server README
- [x] 更新项目总 README 与规划记录
- **Status:** complete

### Phase 4: 本地测试与保护复核
- [x] 安装/使用可用依赖并启动服务
- [x] health/display/image 正确响应
- [x] 正确/错误 device 凭据测试
- [x] 图片尺寸、PNG 和 Content-Type 检查
- [x] 现有前端文件相对 checkpoint 零变化
- [x] 无 Supabase/Stage 2B-2/真实 secret 检查
- **Status:** complete

### Phase 5: 交付与 Nook 实机待验收
- [x] 给出本地启动、环境变量和 Easy Setup 填写说明
- [x] 给出 2–3 个部署方案，不实际绑定/部署
- [x] 明确公网 HTTPS 与 Nook 显示尚待用户实测
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 服务放在独立 `server/` | 与已验收 GitHub Pages 前端清晰隔离 |
| 优先 Python + FastAPI | 后续 Pillow 中文排版路线一致，当前仍保持最小 |
| 本阶段固定图片，不接 Supabase | 将协议/网络/方向问题与动态渲染解耦 |
| 真实凭据只读环境变量 | 单设备最小认证且不泄露到 Git |
| 不写死 Todo provider | API 层只返回 display artifact，方便后续内容来源扩展 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `git ls-remote` 公开仓库失败：Schannel `SEC_E_NO_CREDENTIALS` | 1 | 记录后申请提升网络权限，只读核对 tag/source |
| clone 成功后 `rg` 仍使用项目 workdir，未扫描临时仓库 | 1 | 使用已确认临时绝对路径作为 workdir 重跑，不重复 clone |
| 按常见 Gradle 结构读取 `app/src/main/java` 失败 | 1 | 定位仓库文件后改用实际 Ant 结构 `src/com/bpmct/...` |
| 沙箱网络阻止 pip 下载 | 1 | 经用户批准，仅在项目 `server/.venv` 安装锁定依赖 |
| 最终命令从项目根误写 `./.venv`，随后又从根发现测试 import 约定 | 2 | 按 README 约定进入 `server/` 后重跑，5/5 通过；compileall 已通过 |
| 对图片 endpoint 试探 HEAD 得 405 | 1 | 验收要求为 GET；真实 GET 返回 200/image/png，无需扩大接口 |
| 合并的最终 PowerShell 验收命令 exit 0 但无可见输出 | 1 | 不将其计为通过；拆成独立命令并行重跑，保留各自结果 |
| `git push` 失败：`No configured push destination` | 1 | 当前仓库无 remote；不猜 URL，等待用户提供 GitHub repository URL 后添加 origin/push/验证 |
| 远端逐文件脚本使用 `origin/main:$p`，PowerShell 将冒号参与变量解析，误报全部 missing | 1 | 不采信结果；改用 `origin/main:${p}` 明确变量边界后重跑 |
| 中断后沙箱账户读取宿主账户创建的临时 worktree 触发 `dubious ownership` | 1 | 不修改全局 safe.directory；仅对该临时 worktree 的 Git 命令使用获批宿主权限 |
| 首轮 runtime hash 从 `server/` workdir 运行，根文件被解析成 `server/index.html` 等并误报差异 | 1 | 不采信该项；改从 worktree 根以绝对路径重跑，其他检查结果保留 |
| 多文件 planning 补丁的 hunk 分隔格式错误，补丁未生效 | 1 | 读取准确片段后拆为规范 update hunks 重试 |
| 多文件 planning 补丁再次因空 hunk 结束符失败 | 2 | 改用三个完全独立的 apply_patch 调用，不再组合多文件 hunk |

## Scope Guard
- 不读取 Supabase、不实现动态文字渲染/诗词/AI。
- 不修改现有 login/editor/display/Auth/screen-store/Supabase SQL。
- 不实际部署、绑定收费服务或引入 Worker/Edge Function。
- 不继续 Stage 2B-2。

## Checkpoint & Push Closeout

### Phase 1: Git、diff、secret 与回归检查
- [x] 核对 status/diff/预期文件
- [x] 确认 `.env`、设备真值、API key、Supabase secret 等未被跟踪
- [x] compile、unittest、`git diff --check`
- [x] Stage 1 保护文件相对 `becdc39` 零业务变化
- **Status:** complete

### Phase 2: Koyeb 部署前检查
- [x] 确认 root/build/start/health/env 配置
- [x] 确认 `PUBLIC_BASE_URL` 两阶段填写方法
- [x] 复核 requirements、路径、scale-to-zero 与 TLS 实机风险
- **Status:** complete

### Phase 3: Checkpoint 与 push
- [x] 更新记录但不改业务实现
- [x] 创建 `feat: add stage 2B-1 BYOS test server`
- [ ] push 当前分支并验证远端 commit
- [x] 最终 git status clean
- **Status:** blocked on missing GitHub remote URL

## Remote Reconciliation

### Phase 1: 添加与读取远端
- [x] 添加 `origin=https://github.com/fltp777/dorm-todo-screen.git`
- [x] fetch origin，不修改远端
- [x] 核对默认分支、main/master、共同祖先与最新 commits
- **Status:** complete

### Phase 2: 树内容与安全整合判断
- [x] 核对 origin/main Stage 1 runtime 完整
- [x] 比较本地/远端路径布局和差异
- [x] 确认无 secret、无 Auth/Supabase/RLS 非预期差异
- [x] 因历史不相关而停止，提出 origin/main 基础上的映射集成分支/PR 方案
- **Status:** complete — unsafe to directly merge/push

### Phase 3: 安全 push 与远端验证
- [x] 从 origin/main 创建映射集成分支，不直接修改 main
- [ ] 验证后 push 集成分支并创建/准备 PR
- [ ] fetch/ls-remote 验证远端 hash
- [ ] 确认 Stage 1 + server 共存且本地 clean
- **Status:** in_progress — user approved mapped branch + PR plan

## PR Integration Run
- Planning checkpoint：本地 master `2ddad94 docs: record GitHub remote reconciliation`。
- Integration branch：`codex/stage-2b1-main-integration`，base `origin/main@66c8ff2`。
- Mapping：仅将已跟踪的 `dorm-todo-screen/server/**` 映射为根 `server/**`，并复制 README/task_plan/findings/progress；未复制外层目录。
- [x] 验证 runtime blob、server 完整性、secret、compile、unittest、祖先关系
- [x] 暂存后验证完整 diff 与 `git diff --check`
- [ ] 创建 integration commit
- [ ] push 分支并准备/创建 PR
