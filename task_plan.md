# Task Plan: Stage 2B-2 实机验收 checkpoint

## Stage 2C 夜间长睡眠 / 动态 refresh_rate（2026-10-21）

**Goal:** 在不改变图片、版式、签名、缓存、Supabase、Nook 客户端或 Render 配置的前提下，令 `/api/display` 以 Asia/Shanghai 业务时间返回动态 `refresh_rate`：07:10–22:39 为白天 interval，其他时刻精确睡至下一次 07:10。

- [x] 从已含 Stage 2C 的最新 `origin/main` 创建 `codex/night-sleep` 分支
- [x] 新增纯 schedule 函数与异常 fallback，不改变 API contract
- [x] 添加边界、跨日/月/年与 route fallback 测试
- [x] 更新必要文档与 planning 记录，运行完整本地回归

**Status:** complete — 本轮本地实现/测试已完成；用户现已授权仅做本分支的 commit/push 收尾。不部署、不 merge、不改 Supabase，也暂缓 180° 旋转。

**Error note:** 根 checkout 是旧 `master` 且含用户既有未提交 planning 文档，未触碰；受限沙箱拒绝根仓库 `FETCH_HEAD` 写入，已在获授权的本机 Git 环境执行只读 fetch 后确认 `origin/main` 包含 Stage 2C。Windows Python 未安装 IANA `tzdata`，首次 `ZoneInfo("Asia/Shanghai")` 导入失败；已改用项目现有的显式 UTC+8 named timezone，避免 host tzdata 依赖。一次仅用于报告的内嵌 f-string 表格命令转义失败，改用 here-string 后正确输出，未影响代码或测试。本轮 Git 收尾起始时有一次只读 Git/status 命令误在 skill 目录运行并返回“not a git repository”；未修改项目，随后已在本 worktree 正确重跑。

## Stage 2C Git 收尾（2026-10-20）

**Goal:** 用户已人工执行并验证 Stage 2C Supabase migration；清理纯本地预览产物，纳入正式 Flow/易经/迁移代码与数据库，完成最终回归，创建 commit 并仅 push 当前工作分支。

- [x] 检查 worktree、正式 JSON 路径/原始 SHA-256，区分正式源文件与实验 preview
- [x] 删除 fixed-v2/local preview 源与生成 PNG，并以 `server/.gitignore` 排除可再生 preview 输出
- [x] 暂存正式 Stage 2C 文件，确认 JSON 已 Git tracked
- [x] 完成 compile、unittest、JS、diff、secret 与 450 页目录复核
- [x] 创建 Stage 2C commit，non-force push 当前分支并确认远端

**Status:** complete — `b5263a218cf1b231968a79315def3c1282bfcf90` 已 non-force push 至 `codex/battery-display`，随后作为 PR #5 merge 到 `origin/main`；用户报告 migration 已人工执行并验证。

**Error note:** linked worktree 的 `.git/worktrees/...` 元数据在受限沙箱内拒绝 `git fetch` 的 `FETCH_HEAD` 与 `git add` 的 `index.lock` 写入；经用户授权在本机正常 Git 环境中完成，未使用 force。一次目录统计从仓库根导入 server module 而找不到 `yijing_catalog`；改从 `server/` cwd 后通过，未改代码。

## Stage 2C Right Reminder Gap and Yijing Glyph Width Review（2026-10-02）

**Goal:** 保持已冻结的 Flow 左栏、shared `left_font_size`、动态 divider、数据库、footer 与服务链路，只修正右栏标题到第一条正文的实际 bbox 间距，并生成卦象横向宽度 A/B/C 候选及 production 预览。

- [x] 恢复当前 Flow renderer、测试与既有 planning 状态
- [x] 以与 draw 相同的粗体 bbox 测量右栏标题，并应用 16 px 正文间距
- [x] 生成 current/+15%/+20%/+25% 卦象横向比例对照图；production preview 暂用 +20% 候选
- [x] 增加局部回归测试，生成五张 production preview 并完成验证

**Status:** complete — user selected and froze +20% (`1.20`) glyph width and 16 px reminder title/body gap; no deployment, migration, commit, or push.

## Stage 2C Frozen Layout and Deployment-Readiness Audit（2026-10-20）

**Goal:** 将验收的 `YIJING_GLYPH_WIDTH_SCALE=1.20` 与 `REMINDER_TITLE_BODY_GAP=16` 固定为 production 默认，冻结版式；核对正式易经 JSON、migration、refresh/cache/signed URL 与 Git 部署准备，生成最终五张 preview，不执行外部写入。

- [x] 确认最终视觉参数与冻结范围
- [x] 将原始正式易经 JSON 原样复制到本 worktree 的 `yijing database/`，并以 SHA-256 确认字节一致；loader 只解析该 repository-root 相对路径
- [x] 生成 final 命名 preview、完成目录/migration/refresh/cache 审计与完整离线回归
- [x] 将正式 JSON 放入当前 Git worktree 的稳定可部署路径，并移除 loader 对共享上级目录的运行时依赖
- [x] 审计 display pages、position 边界、migration、refresh/cache/signed URL 与 artifact 上限
- [x] 生成 `01_final` 至 `05_final` preview，并运行全部部署前检查

**Status:** complete — JSON 位于本 worktree 的 repository-root 相对部署路径，loader 无 parent fallback；它仍是未跟踪工作文件，下一次经人工确认的 commit 才会使 Render clone 可见。最终五图、71/71 unittest、compileall、JS syntax、preview 验证、diff/secret 审计均已完成；没有外部写入。

## Stage 2C Flow Typography Fit Efficiency Audit（2026-10-02）

**Goal:** 保持现有 Flow 设计、动态 divider、右栏、footer、数据库与服务链路不变，只核对 production shared-font 高度预算；若发现明确的重复尾部 leading，则做最小测量/绘制一致性修正。

- [x] 对五个 production sample 逐项输出最终字号与 `S+2` 高度预算
- [x] 确认 production 与历史 local preview 的内容/测量差异来源
- [x] 修正左栏块预算对最后一行 trailing leading 的重复计入；不改安全边界
- [x] 重新生成五张 production preview，完成 68/68 unittest、compile、图像与 diff 检查

**Status:** complete — current selected shared sizes are 30 / 40 / 26 / 24 / 22; no deployment, migration, commit, or push.

## Stage 2C Flow Layout 与正式易经数据库接线（2026-10-02）

**Goal:** 用户已明确撤销 fixed v2 作为正式默认的决定。将 production renderer 改为左侧连续 flow layout，并以工作区 `yijing database` 的真实 64 卦数据生成有限、可手动定位的页面序列；保留既有 Stage 2B API、签名 URL、缓存和预旋转协议，必要时仅为“本次成功 `/api/display` 请求时间”做最小且有界的缓存/version 扩展。不得连接真实 Supabase、执行 migration、部署、commit 或 push。

- [x] 记录方向变更并恢复当前本地工作树、旧 fixed-v2 接线与规划记录
- [x] 完整审计易经数据库文件、实际 schema、64 卦顺序与可用爻/用九/用六字段
- [x] 以真实数据替换两页 mock catalog，并让 provider/editor 的 position 共享同一扁平序列
- [x] 将 production portrait renderer 切换为 flow layout；保留 800×600 预旋转输出、右栏与 footer 边界
- [x] 为认证成功请求时间设计有界 artifact/version/signed-url 传递，并补覆盖性测试
- [x] 生成五张指定 production review PNG，逐项记录字号、动态分线、总高度和 overflow
- [x] 运行 Python/JS/图像/回归/secret/diff 检查；仅保留本地未提交变更

**Status:** complete — flow is the production renderer direction locally. Earlier fixed-v2 local artifacts remain uncommitted historical/preview material, but production code has no fixed y=373 path. No external change was made.

## Stage 2C Flow Shared Typography Correction（2026-10-02）

**Goal:** 保持 flow、动态 divider、右栏、数据库、API、signed URL、cache、Supabase、电量和 footer 全部不变，只把左栏改为一个共享 `left_font_size` 的整体 fit。

- [x] 标题、待办、易经 heading/卦名/爻名与全部易经正文统一使用同一候选字号
- [x] 仅以粗体表达左栏标题层级，不再以字号形成独立层级
- [x] 重新生成五张 production flow preview，并改为 shared-font metadata
- [x] 增加 left typography equality tests；完成 compile、66 tests、图像、JS、secret、diff 检查

**Status:** complete — no deployment, migration, commit, or push.

**Error note:** 本轮第一次 compile 命令从 `server/` cwd 仍使用 `server\\renderer\\...` 路径，产生路径不存在；生成脚本随后正常运行，最终编译需使用 server cwd 下的相对路径。

**Error note:** 首次 Python schema inspection 把顶层 `trigrams` 当作 list 索引，实际为命名 dict，因而出现 `KeyError: 0`；未写入任何文件，随后已按实际 schema 成功读取首卦、末卦与两个 special-use 记录。首次 renderer smoke command 从 worktree root import `renderer`，以及 `ZoneInfo("Asia/Shanghai")` 在本机缺少 tzdata 时均失败；前者已从 `server/` 重跑，后者已换为不依赖 tzdata 的固定 UTC+8。一次包含多文件 hunk 的 README patch 因末尾上下文不精确而整体未应用；已拆成定点 patch。一次临时字号探查的 PowerShell/Python 转义错误只产生 SyntaxError，未写入文件。

第二次全量 unittest 从 worktree root 使用 `-s server/tests` 启动，既有 tests 预期 cwd 是 `server/`，因此出现 five `ModuleNotFoundError`；compile、JS、五图检查、diff 和凭据检查仍完成。该失败不作为代码回归结果，后续将从既有约定的 `server/` cwd 重跑。

## Fixed v2 Production Renderer Wiring（2026-10-02）

**Goal:** 将已验收的 fixed v2（x=392、左分线 y=373、footer y=746）接入本地 production renderer；待办和易经分别自适应，右侧提醒独立。补足最小状态/编辑器接线、schema migration、生产回归 PNG 与自动测试。保留 flow preview 但不设为生产默认；不部署、不连接真实 Supabase、不 commit/push。

- [x] 恢复现有 preview、production renderer、editor/store 与仓库内 schema 资料
- [x] 为 preview/production 抽取共同 fixed-v2 layout helper，并补 fixed-v2 双压力回归
- [x] 以最小字段扩展 screen state、provider 与 editor 的 todo/reminder/yijing position 接线
- [x] 生成五张 production preview，覆盖 regular/压力/边界和 overflow detection
- [x] 完成自动测试、compile/diff/secret/范围检查与文档记录

**Status:** complete — fixed v2 is the only production layout mode. The local-only migration remains unexecuted; no Render, Supabase, Nook, commit, push, or deployment action was performed.

**Error note:** 本轮首次 session-catchup 直接执行 `.py`，PowerShell 因权限拒绝而未运行；后续已通过明确的 Python 解释器调用（无未同步报告）完成。一次 editor JS 的组合 patch 因初始化段上下文不完全匹配而未应用；已读取后改为替换完整小文件，不重复该 hunk。首次全量 unittest 在新 renderer 接线后为 48 pass / 10 error：旧 `test_renderer` 断言已移除的单段 `layout_text/footer_layout`，provider fixture 仍是两字段旧 row；这不是 runtime 异常，将迁移测试至 fixed-v2 契约和完整新 row 后重跑。首轮 secret 文件名扫描把前端的 `service_role` 防泄露注释误识别为 secret；不采信该结果，将改为精确检查 `.env`、真实 `sb_secret_` 值及 credential assignment，避免重复宽泛 marker 扫描。第二次 assignment regex 因 PowerShell/PCRE 引号组合造成 character-class 编译错误，命令仍继续执行，结果不计入通过；改用不含引号 class 的逐项固定模式并检查 `rg` exit code。第三次 device env 扫描未正确排除允许的 `server/.env.example`，故不采信；`.env` 已单独确认不存在，下一次只将 `.env.example` 作为允许的唯一 env 文件处理。

## 左侧连续流式信息区 Preview（2026-10-02）

**Goal:** 只扩展本地 `server/layout_preview.py` 与 `server/layout_previews/`。左侧取消固定横向分栏，让待办与易经在同一连续区域使用共享的 40→22 px 正文字号；保留 x=392 竖线与 y=746 状态栏，不修改生产 renderer/API/Supabase/签名/cache，不部署、不 commit/push。

- [x] 恢复现有 v2 preview、字体与 1-bit 600×800 基线
- [x] 增加 flow 测量、动态分隔线、统一左侧正文字号及五个请求 PNG
- [x] 复核 normal/压力图、元数据、边界与同 v2 的差异
- [x] 运行 preview 完整性和项目回归；记录结论并保持本地未提交

**Status:** complete — 5 requested flow PNGs produced; all are 600×800 mode-1 and unclipped. The 58 existing tests pass; no production file was changed, committed, pushed, or deployed.

**Error note:** 初始 PowerShell `rg` 多 pattern 命令含 `|`，被 Windows 命令包装层当作管道解析，未得到目标函数的可靠检索结果；后续不用该形式，改用脚本内已读取的定点上下文和无管道检索。一次跨两份 planning 文档的 patch 因 `progress.md` 标题与预期不一致而整体未应用；已拆成两份精确补丁，未丢失记录。最终从 worktree 根复核 PNG 时误用了从 `server/` 起算的 venv 相对路径，PowerShell 未找到解释器；将改用根目录正确的两级上溯路径，不重试错误路径。

## 三区布局 E1/E2/E3 与自动缩放预览（2026-10-02）

**Goal:** 仅扩展 `server/layout_preview.py` 和本地 preview 输出，固定 600×800 三区/状态栏 geometry，比较 E1/E2/E3 大字号与逐区域自动缩放；不改生产 renderer、API、Supabase、签名、cache、Render 或 Nook。

- [x] 恢复上轮 preview 工作树、固定几何与字体基线
- [x] 新增 E1/E2/E3 的整卦/单爻固定字号预览
- [x] 新增常规、待办压力、易经压力的自动缩放预览与字号元数据
- [x] 验证 1-bit/600×800、悬挂缩进、边界、回归和 diff
- [x] 记录字号比较与推荐；保持未提交、未部署

**Status:** complete — 10 requested E/auto PNGs generated and reviewed locally; no production changes.

**Error note:** Windows `cmd` 将带 `|` 的 `rg` 多模式 pattern 解析为管道；带空格的 quoted regex 也被 wrapper 拆分；不会重试同一形式，后续使用无空格单模式定点检索。一次 metadata 检查在 `server/` workdir 仍使用 `server/layout_previews/...` 而失败，改为 `layout_previews/...` 后复核成功。

## Equal-height / No-label-column Auto Preview v2（2026-10-02）

**Goal:** 将左侧分线移至 y=373，取消易经 label/body column，并生成四张 `layout_auto_v2_*` 本地自动缩放比较稿；不改生产 renderer、API、Supabase、签名、cache、Render 或 Nook。

- [x] 固定 v2 geometry：x=392、y=373、footer y=746；右栏完整贯穿主体
- [x] 改为 `【标签】正文` 普通 340 px 段落，移除预览中的 label 字号/粗体/悬挂缩进
- [x] 生成常规整卦、单爻、8 条待办压力及长易经压力四张 v2 PNG
- [x] 完成逐区域 2 px auto scale、标点换行修正、行数/裁断 metadata 和图面复核
- [x] compile、PNG 完整性、58/58 unittest 与 diff check；保持未提交、未部署

**Status:** complete — normal todo=42 px, todo stress=26 px, normal hexagram body=34 px, long Yijing body=24 px; all v2 previews are unclipped.

**Error note:** 一次组合 planning/README patch 因已更新的 plan checklist 上下文不匹配而整体未应用；改为精确段落补丁，不重复同一 hunk。

## Nook 600×800 分区信息屏版面与字号测试稿（2026-10-02）

**Goal:** 仅生成可人工比较的 600×800 portrait、1-bit PNG 版面测试稿；不修改生产接口、动态 renderer、Supabase、缓存、签名 URL、Nook 或 Render 配置。

- [x] 恢复工作树并定位实际 `codex/battery-display` worktree
- [x] 核对现有 Todo renderer、字体资产、800×600 预旋转规则和测试基线
- [x] 新增独立 layout preview 脚本与四组整卦/单爻预览及压力测试
- [x] 检查所有输出尺寸、黑白模式、区域边界、悬挂缩进与溢出策略
- [x] 记录字号、坐标、字体与人工比较结论；不提交、不部署

**Status:** complete — 9 local preview PNGs generated and reviewed; production code paths remain untouched.

**Notes:** 首次 session-catchup 的带引号 Windows `cmd` 调用把脚本路径拼进 workdir，未执行；改为无空格路径的独立调用后继续。一次三文件 planning patch 因 findings 标题与旧上下文不同而未应用；改为三个定点 patch 后成功，未覆盖任何记录。最终枚举时曾从 worktree 根误用 `layout_previews/`，改为 `server/layout_previews/` 后确认全部 11 个预览目录文件。

## 电量显示功能设计审计（2026-09-21）

**Goal:** 只读核对 TRMNL Nook Client v0.16.0 的实际电池请求 header、当前 FastAPI 与动态 PNG 的版本/缓存边界，并给出最小电量显示方案；不修改业务代码、配置、Supabase、Nook 或部署，不提交。

- [x] 恢复工作树并确认当前 checkpoint 分支干净
- [x] 从 v0.16.0 实际源码确认 `/api/display` 请求 header、数据格式与深度休眠路径
- [x] 核对 FastAPI routes/service/content/cache/renderer/tests 是否已读取设备状态
- [x] 审计 content version、artifact cache、signed URL 与电量刷新耦合
- [x] 制定最小视觉、缺失值、文件改动及测试方案
- [x] 记录审计结论；保持业务代码与 Git 历史不变

**Status:** complete — read-only design audit; no implementation started.

## Nook 电量显示本地实现（2026-09-21）

**Goal:** 在 `origin/main@f3a6551` 的独立 `codex/battery-display` 分支实现 Nook request-only 电量 footer、精确电量 display version 与已签名 `b` URL 参数；仅本地代码、测试和文档，不部署、提交或 push。

- [x] fetch 最新 origin/main，保留三份未提交设计审计记录并建立独立分支
- [x] 实现严格 `Percent-Charged` parser 与 API → DisplayService request state
- [x] 实现 content/display version 分层、已签名 battery state 和 cache-miss 重建
- [x] 实现不重叠的中文右下 footer 与低电量文案
- [x] 增加 parser、renderer、cache/version、signed URL、API 与回归测试（首轮全量 58/58）
- [x] compile、unittest、diff check、secret scan、Stage 1/2B 回归；更新文档（58/58 passing）

**Status:** complete — LOCAL IMPLEMENTATION ONLY; 58/58 tests and regressions pass; no deploy, commit or push.

## Nook 电量显示提交与 PR（2026-09-21）

- [x] fetch origin；确认 `origin/main@f3a6551` 未在本地开发期间前进
- [x] 确认 `codex/battery-display` 直接基于当前正式 main，不需 rebase/merge
- [x] 复跑完整验收、diff 与凭据扫描（compile + 58/58、diff、Stage 1/2B 回归通过）
- [x] 创建 `feat: add Nook battery status to todo screen` commit（本次 checkpoint 即将创建）
- [ ] push `codex/battery-display`，只准备 PR 到 main，不 merge

**Status:** in_progress — LOCAL IMPLEMENTATION ONLY; no deploy or main push.

**Note:** 一次 `git diff -G` 私钥模式因 Windows `cmd` 将含空格正则拆分而失败；已改用无空格 token/secret/signed-URL 模式与文件范围复核，未产生文件改动。

**Note:** 一次 Windows `cmd` 全局检索将 `|` 解释为管道，未读取到目标集合；已改为 compile/test 的定点验证方式，未改动任何文件。

**Test note:** 首轮测试发现当前 worktree 缺少 FastAPI/httpx 虚拟环境；同时新增 direct-service 测试暴露 cache-hit 未显式校验 battery state，以及测试 fake renderer 期望值过时。前者已将 `battery_state` 固化到 artifact 并在 cache hit 校验，后者已更新；随后将用现有项目 venv 重跑全量测试。

## Stage 2B-2 Verified Checkpoint (2026-09-03)

- [x] fetch 并确认最新 `origin/main@fb5cb277e6d05b8b16a9b860929024ffc29db9ce`
- [x] 确认实现提交 `c4bcddc53b98fbdbe0d0c544aae45a8f3e14bce1` 已进入 main
- [x] 从最新 origin/main 创建干净的 `codex/stage-2b2-verified-checkpoint`
- [x] 更新 README、server README 与 planning 记录，只记录实机验收状态
- [x] 复核 diff 仅含文档，并完成 secret、Stage 1 与 server 业务代码保护检查
- [x] 创建 `chore: checkpoint verified stage 2B-2` commit
- [ ] push 独立 checkpoint 分支并准备 PR 到 main（不 merge）

**Status:** checkpoint_ready — 文档、secret 与回归检查通过；只待提交、push 独立分支并准备 PR，不修改或部署任何业务代码。

## Stage 2B-2 Local Implementation (2026-09-01)

**Goal:** 在 `a4b4a74` 基线上完成 TodoProvider → NormalizedContent → 中文黑白 renderer → 两版本缓存 → HMAC 短期图片 URL 的本地实现与自动测试；不使用真实 secret、不部署、不修改 Stage 1/RLS/Nook。

- [x] 完整读取要求、恢复上下文、建立 `codex/stage-2b2-local` 隔离 worktree
- [x] 复核新版 Supabase secret REST header、官方 Noto 字体与许可证
- [x] 实现 content/provider/renderer/signing/cache/config/API
- [x] 扩充 mock/unit/API/security/regression 测试（48/48 passing）
- [x] 更新 README、server README 与 planning 记录
- [x] compile、全部 unittest、diff check、secret scan、Stage 1 blob 回归

**Status:** historical local implementation checkpoint — 此后已完成部署及 BNRV300 实机验收，当前状态见上方 verified checkpoint。

## Stage 2B-2 Checkpoint, Remote Integration & PR (2026-09-02)

- [x] 恢复 worktree 并核对未提交实现范围
- [x] fetch origin/main，验证当前分支祖先关系与无远端分歧（main/HEAD/merge-base 均为 `a4b4a74`）
- [x] 重跑 compile、48 tests、diff check、secret/font/runtime/Stage 2B-1 回归
- [x] 暂存后核对最终 PR diff、路径层级、无删除/secret（23/23 allowlist）
- [x] 创建 `feat: add stage 2B-2 dynamic todo rendering` commit
- [x] push `codex/stage-2b2-local`，验证远端 hash
- [x] 创建 PR 到 main，并复核最终 diff；实现已由 merge commit `fb5cb27` 进入 main

**Status:** complete — implementation commit `c4bcddc` 已通过 PR 安全集成到 main。

## Goal
为现有 GitHub repository 添加 origin，核对本地 master 与远端默认/main 历史和 Stage 1 runtime 完整性，仅在可证明安全时将 Stage 2B-1 整合到远端主分支；绝不 force push、删除分支或进入 Koyeb/Stage 2B-2。

## Current Phase
Stage 2B-1 COMPLETED / VERIFIED；Stage 2B-2 COMPLETED / VERIFIED。当前只记录真实端到端实机验收结果并建立文档 checkpoint。

## Real-device Acceptance Checkpoint (2026-09-01)

- [x] Nook Simple Touch BNRV300 + Phoenix Phase 4 / FW 1.2.2 实机通过
- [x] TRMNL Nook Client v0.16.0 Self-Hosted / BYOS 最小闭环通过
- [x] Render Free Web Service（Singapore）公网 `/health`、`/api/display`、`/screen/test.png` 通过
- [x] 手机热点访问、认证、PNG 下载和显示通过
- [x] 800×600 预旋转图经客户端旋转后正确显示为 600×800 竖屏
- [x] 四角方向、双边框、无明显裁切及中文显示通过
- [x] 当前刷新测试值记录为 300 秒
- [x] Stage 2B-2 部署与实机验收：真实 Supabase 动态内容、signed image URL 与 BNRV300 显示链路通过
- [ ] 校园网 PEAP 验证（后续独立任务）
- [ ] Render Free spin-down / cold-start 长期表现验证

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
| 测试补丁在同一 patch 中同时 delete/add `test_app.py`，验证失败且未生效 | 1 | 拆为新增测试文件与单独更新现有测试文件，不重复同一路径操作 |
| 首轮 47 tests：cache-miss/stale 两项失败 | 1 | `ArtifactCache.__len__` 使空 cache 为 falsy；将 app 注入从 `cache or ...` 改为显式 `cache is not None` |
| 空状态黑白测试期待 0/255，但 Pillow mode `1` 的 `getcolors()` 返回 0/1 | 1 | 保持 renderer 严格 mode `1`，修正测试断言为 `{0, 1}` |
| PNG 重新打开后的 mode `1` `getcolors()` 返回 0/255，与内存图的 0/1 表示不同 | 2 | 断言同时接受 Pillow 两种二值表示，并继续强制 image.mode == `1` |
| 最终字体哈希命令已在 `server/` workdir，却再次使用 `server/assets/...` | 1 | 其他验收结果保留；改用 `assets/fonts/...` 正确相对路径单独重跑哈希 |
| 沙箱账户执行 `git ls-remote` 遇到 Schannel `SEC_E_NO_CREDENTIALS` | 1 | fetch 已用获批宿主权限成功；远端分支/哈希核对改为统一使用获批网络权限，不重复沙箱调用 |
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
