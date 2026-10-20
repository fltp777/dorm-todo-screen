# Progress Log

## 2026-10-20 — Stage 2C Git 收尾（进行中）

- 用户报告并确认 Stage 2C migration 已人工执行：`main.text` 和 `updated_at` 保留，`daily_reminder_text=''`、`yijing_position=0` 正常；本轮不再操作 Supabase。
- 已清理不应提交的 fixed-v2/preview-only 源、所有生成 PNG 与 metadata；`server/.gitignore` 现忽略 `layout_previews/` 和 `production_previews/`。保留 `generate_flow_production_previews.py` 作为冻结 Flow renderer 的本地回归工具。
- 正式数据库仍为 137,592 bytes，SHA-256 为 `B606AEAEED14B9CB9AF160B04B59A6BB23876FED12CF245BC9E03A94AF2CBD05`；当前位于 repository-root 相对部署路径，下一步暂存、完整回归、commit 与 non-force push。
- 已暂存 28 个正式 Stage 2C 路径，正式 JSON 已为 Git index blob；未暂存/未提交 preview PNG、metadata、fixed-v2 helper 或实验 preview script。
- 提交前回归通过：Python compile、64/384/2/450 catalog 统计、71/71 unittest、`editor.js`/`screen-store.js`/`yijing-content.js` syntax、staged/working `git diff --check`。敏感信息扫描无 `.env`、私钥、JWT 或真实 secret；唯一匹配为 `.env.example`、README 和测试的 placeholder/fake value。

## 2026-10-02 — Stage 2C Right Reminder Gap and Yijing Glyph Width Review（进行中）

- 已恢复 production Flow renderer 与当前 planning 状态。范围只包含右栏标题/正文实际 bbox 间距和卦象横向比例候选；左栏 fit、动态 divider、footer、数据库及服务链路均冻结。
- 已生成五张 production preview 与卦象对照图。图面复核确认右栏间距和 +20% 首行均正常；对照图第一版的长宽度说明文字跨列重叠，需要改为更短的两行标注后再验收。
- 已将对照图改为简短的 `六NN 三NN` 宽度标注，四列可清晰比较。production preview 的右栏首项实际间距为 16 px，reminder 仍为 50 px，最后一项 bbox bottom=454，未接近 footer limit=730。
- 用户已最终选择并冻结 +20%（`1.20`）glyph width 与 16 px reminder title/body gap；五张 production preview 均重新生成，71/71 unittest、compileall、root JS syntax 与 `git diff --check` 通过。未 deploy、migration、commit 或 push。

## 2026-10-20 — Stage 2C Frozen Layout and Deployment-Readiness Audit（进行中）

- 用户已正式选择 glyph width multiplier `1.20` 与 reminder title/body gap `16 px`，并冻结 Flow 版式。
- 已把未修改的同一 JSON 原样放入本 worktree 的 `yijing database/`，以 SHA-256 验证一致；loader 已移除父目录 fallback，只使用仓库根相对路径。该 JSON 仍未 Git 跟踪，后续未获用户授权前不会 commit/push。
- 最终审计完成：64 卦、384 常规爻、乾用九/坤用六、总 450 页与 0..449 position 通过 runtime/tests 核对；编辑器边界无循环，renderer 不改变 position。迁移仅新增 daily reminder/Yijing position 及 authenticated 列 grant，不动 RLS/anon。
- 已生成 `01_final_*` 至 `05_final_*` 五张冻结版 preview：均为 600×800 1-bit，无 overflow/truncation。服务端 footer 的 refresh minute 已确认来自成功 display 请求的 UTC 时钟、显示为 UTC+8，并进入 version/signed URL/cache-miss 重建路径；cache 保持两版本有界。
- 最终离线验收：compileall PASS、unittest 71/71 PASS、`editor.js`/`screen-store.js`/`yijing-content.js` syntax PASS、preview mode/size/metadata PASS、`git diff --check` PASS。未执行 migration、deploy、commit、push 或 merge。

## 2026-10-02 — Stage 2C Flow Typography Fit Efficiency Audit（完成）

- 对五个 production sample 复核最终 shared `left_font_size` 与 `S+2` 高度预算；确认可用区 y=22..732（710 px）和 footer 安全边界没有重复扣除。
- 找到唯一明确的效率问题：块高度把最后一行 trailing leading 重复计入。已用 `line_box_height` / `wrapped_lines_height` 修正左栏 title、todo、易经 heading/body 的预算及 draw 边界；未改动态 divider、右栏、footer、API、数据库、签名或 cache 设计。
- 重新生成五张 `server/production_previews/01_flow_*.png` 至 `05_flow_*.png`：shared 字号为 30、40、26、24、22；均为 600×800、1-bit、无 overflow/truncation。
- 新增预算回归测试；从 server cwd 全量 unittest 68/68 PASS，compileall PASS。仍未 deploy、migration、commit 或 push。

## 2026-10-02 — Stage 2C Flow Layout 与正式易经数据库接线（进行中）

- 用户已将正式方向改为 flow layout，并要求接入已导入的真实易经数据库；本轮允许本地 production code 与测试变更，但禁止执行 Supabase migration、连接线上凭据、部署、commit、push 或修改 Nook/TRMNL。
- 已恢复当前 local-only worktree 与 planning 记录，开始审计数据库 schema 和现有 renderer/cache/signing 接线；fixed v2 仅作为待替换的本地历史实现保留。
- 已完成 production flow 接线：`TodoRenderer` 不再导入 fixed-v2 helper 或使用固定 y=373；共享 flow helper 只固定 x=392、y=746，待办完结后计算 1 px divider。右栏与 800×600 预旋转路径保留。
- 已从真实 JSON 构建 450 个 Yijing pages（64 整卦、384 常规爻、乾用九、坤用六），provider 验证正式范围，editor 由同一 JSON 异步加载导航 metadata。未更改任何经典正文。
- 已把 server-confirmed `/api/display` 时间以 UTC+8 `更新 HH:MM` 接入 renderer；有界 cache/version/HMAC URL 新增签名 `r` minute state，未改变 Supabase 字段或 Nook 请求协议。
- 已从正式 renderer 生成并目视检查五张 `01_flow_…` 至 `05_flow_…` 预览和 `flow_metadata.json`。初轮/定点测试已通过，正在完成全量 compile、JS、image、secret 与 diff 验收；未执行 migration、部署、commit 或 push。
- 最终验收通过：`compileall`、全部 66 个 unittest（API 18 + provider/catalog/security 35 + renderer 13）、根目录 JS `node --check`、五张 preview 的 mode `1`/600×800 校验、`git diff --check` 与 `.env`/非 placeholder `sb_secret_` 模式扫描均通过。当前 `git status` 按用户要求保持本地 dirty；未执行 migration、未部署、未 commit、未 push。

## 2026-10-02 — Stage 2C Flow Shared Typography Correction（完成）

- 按用户确认的 shared-size coupling 修正左栏：标题、待办、易经 heading/卦名/爻名与全部正文统一为一次求解的 `left_font_size`；仅粗体表达层级。右栏、divider、footer、数据库、API、签名/cache、Supabase 未改。
- 重新生成五张 production preview：shared left font 28、40、24、24、22；reminder 均 50；divider y 215、340、301、185、283；全部 600×800 mode-1、无 overflow/truncation。
- 67/67 unittest、compileall、JS syntax、图像校验、secret scan、git diff --check 通过。极端 160 行无法在共享最小字号完整容纳时改为安全报错，绝不截断；本轮仍未 migration/deploy/commit/push。

## 2026-10-02 — Fixed v2 Production Renderer Wiring（进行中）

- 用户已明确选定 fixed v2 为生产默认，flow 仅保留本地极端内容候选。本轮可修改正式 renderer/最小状态接线，但不得部署、commit、push 或改动线上 Supabase。
- 已核对：当前网页/store 与 Supabase provider 只使用 `screen_state.text`；无提醒/易经位置字段或正式易经 catalog。将通过本地 migration 和两页用户已给测试内容完成最小验证，不新增表、不改 RLS。
- 已生成第一版五张直接经 production renderer 绘制的 upright review PNG；fixed-v2 双压力 todo=26 px、Yijing=24 px，完整且无 fallback。图面检查发现 `☰` 缺字方框，已按既有 preview 的 1-bit 线条兼容策略修正 production header，正在重新生成复核。
- fixed v2 production wiring 完成：新增 shared layout helper，renderer 默认固定 x=392/y=373/footer=746，各区独立 fit；flow 未被 production 导入。最小字号仍 overflow 时只记录 warning 并以省略号保护边界，不自动切换 flow。
- 已加入本地待执行 `supabase/stage-2c-fixed-v2-state.sql`、每日提醒与手动易经 position editor controls、两页最小乾卦 catalog；未执行 SQL，未连接线上 Supabase。未改 API、签名算法、cache key、Nook 或 Render。
- 最终验证：compileall、66/66 unittest、所有根目录 JS `node --check`、五图重新生成及 1-bit/600×800 metadata、`git diff --check`、secret scan 均通过。未 commit、push 或 deploy。

## 2026-10-02 — 连续流式左区 Preview（进行中）

- 已在 `server/layout_preview.py` 新增纯本地的 flow study：待办/易经正文共享 40→22 px、每次减 2 px 的选择器，标题固定 40 px，右侧提醒保持原独立 50→24 px 规则。
- 已生成请求的五张 `layout_flow_*.png`，并写入 `layout_metadata.json`；当前初检均为完整、不裁断的 600×800、mode `1` PNG。
- 已目视检查常规整卦和双压力结果；尚待逐图复核、与 v2 精确比较及回归检查。未触及生产 renderer/API/Supabase/签名/cache，也未 commit/push/deploy。
- 完成复核：flow normal hexagram=36 px、line=40 px、todo stress=32 px、Yijing stress=32 px、both stress=26 px，五图均无省略或跨区。相较 v2，flow 给长待办 +6 px、给长易经 +8 px，但会使同一待办随易经篇幅缩放，并让动态线在 y=246..402 之间移动。
- 已通过 `compileall`、预览生成及 600×800/mode-1 校验、全部 `unittest` 58/58、`git diff --check`。生产 renderer/API/Supabase/签名/cache diff 为空；只保留本地 preview 脚本、PNG/metadata/说明和 planning 记录，未 commit/push/deploy。

## Session: 2026-10-02 — Nook 600×800 layout preview

- **Status:** in_progress — visual-layout work only.
- 已在 `codex/battery-display` worktree 中核对项目结构、生产 Todo renderer、字体许可、旋转规则与 renderer/API 测试；未改动任何正式业务代码或外部配置。
- 发现父项目根当前是旧 `master` 工作树；预览产物将仅放入拥有现行 renderer 的隔离 worktree，避免误改历史树。
- 首轮预览中 bundled Noto 的 `䷀`/`☰` 为缺字方框，系统 symbol fallback 也不能可靠表现六爻；已改为 preview-only 的 1-bit 乾卦/乾三爻几何线条。未改生产字体、renderer 或依赖；该字体覆盖问题将列入最终观察结果。
- 新增独立 `server/layout_preview.py` 与 `server/layout_previews/`：生成 A/B/C/D 各整卦页、单爻页及一张压力图；所有文件均为未旋转的 600×800 portrait 1-bit PNG，未被 production app 导入。
- 完成脚本 compile、生成后 PNG 完整性检查、既有 unittest 58/58 与 `git diff --check`；未执行 git commit、push、Render 部署、Supabase 或 Nook 操作。
- 已开始第二轮 E1/E2/E3 与自动缩放视觉比较；固定 40 px 标题保持不缩放。发现 40 px 两字标签大于固定 label/body 槽宽，E3 采用 preview-only 竖排标签，自动模式将基于可用宽度降级并记录实际字号。
- 已完成 6 张 E1/E2/E3 与 4 张 auto PNG：常规 auto 为 todo=32/reminder=50/header=40/label=34/body=40；todo stress 为 todo=24 且末行省略；yijing stress 为 body=24 且完整。E3 整卦页触发易经截断；E1 是固定字号中唯一保持常规整卦完整且采用横排标签的版本。
- 第二轮也完成 preview compile、所有生成 PNG 的 600×800/mode-1 检查、既有 unittest 58/58 与 `git diff --check`。未执行 commit、push、部署或任何生产配置操作。
- 第三轮开始：新增等高左区与无标签列 v2 auto preview；首轮图面发现 preview-only 中文逐字换行会孤立行首句读，正以最小禁则修复后重新复核。生产 renderer/API 不受影响。
- v2 复核完成：在 `y=373` 等高左区，常规待办自动使用 42 px、8 条压力待办 26 px 且均无截断；常规整卦正文为 34 px、长文压力为 24 px，均无跨区或状态栏侵入。preview-only wrap 已避免孤立行首标点与不自然 `勿。`/`用` 拆分。

## Session: 2026-09-21 — Nook 电量显示本地实现

- 从最新 `origin/main@f3a6551` 建立独立 `codex/battery-display` 分支，并保留上一轮三份未提交电量审计记录。
- `/api/display` 现严格解析可选 `Percent-Charged`；合法 ASCII 十进制 0–100 进入 display request state，缺失或非法值为 `None`，仅记录不含原值的 warning，正文请求仍可用。
- `NormalizedContent`、TodoProvider、Supabase 表/RLS 与 Stage 1 网页保持不变。content version 仍只来自 `updated_at`；artifact version 额外包含规范 battery state `0..100|none`。
- 签名 URL 由 `v`、`b`、`exp`、`sig` 组成，HMAC canonical message 覆盖 `b`；cache miss 使用已验证的 `b` 重算版本，Todo 已更新时维持 410 stale，provider 失败且无 cache 时维持 503。
- Renderer 始终预留 56 px footer 区，使用现有 Noto Sans CJK SC 18 px 与 44 px 安全边距；方向仍是 600×800 portrait 后 `ROTATE_90` 输出 800×600。
- 最终 compile、58/58 unittest 与 `git diff --check` 通过；Stage 1 runtime 13/13 与 origin/main 无差异，Stage 2B-1 固定校准图/generator 无差异。未部署、未 commit、未 push。
- 凭据复核未发现已跟踪 `.env`、GitHub token 或私钥；`sb_secret_` 仅出现于现有 server-only 配置前缀校验，未记录真实值。

## Session: 2026-09-21 — 电量显示功能设计审计

- 只读确认 `usetrmnl/trmnl-nook-simple-touch@v0.16.0`（tag `a1a102d…`）实际在每次 `ApiFetchTask` 时读取 Android battery level/scale，发送条件性 `Percent-Charged: <0..100 integer>` 与 `rssi: <dBm integer>`；无电压或充电状态 header。
- 常规与深度休眠/闹钟唤醒路径都会进入同一 fetch task。未知 battery 时 header 缺失但请求继续。
- 当前 FastAPI 仅读取 `ID`/`access-token`，没有读取任何 device-state header；现有 content version 只基于 `updated_at`，所以电量变动会复用旧 PNG。
- 设计建议：电量保持 request-only 状态，精确整数纳入 display version；在 HMAC 签名 URL 中加入已签名的非敏感 `b` state，支持 cache miss 的一致重建。缺失/非法值只隐藏 footer，不影响正文。
- 推荐 footer：600×800 portrait 右下、Noto Sans CJK SC 18 px、44 px 右/下边距，正文永久预留约 56 px 底部区域；20/10 两个低电量阈值按用户要求显示提醒文本。
- 未修改业务代码、测试、Render、Supabase、Nook、Git 提交或远端。GitHub 网页源码直读遇到缓存 miss 后，已改用精确 tag 的临时只读 clone 完成核对。

## Session: 2026-09-03 — Stage 2B-2 实机验收 checkpoint

- **Stage 2B-1：COMPLETED / VERIFIED；Stage 2B-2：COMPLETED / VERIFIED。**
- 已确认 `origin/main@fb5cb277e6d05b8b16a9b860929024ffc29db9ce` 包含 Stage 2B-2 实现提交 `c4bcddc53b98fbdbe0d0c544aae45a8f3e14bce1`，并从最新 main 创建独立文档 checkpoint 分支。
- 用户已真实验证手机 editor → Supabase `screen_state.main` → Render/FastAPI → provider/content/renderer → signed PNG → TRMNL v0.16.0 → BNRV300 的完整链路。
- 动态图片来自真实 Supabase，浏览器和 Nook 均成功获取；Nook 显示真实手机输入内容，中文/英文及手动换行正常。
- 保持 Stage 2B-1 已验证的 800×600 预旋转逻辑不变；本轮不修改 server、renderer、signed URL、网页、Supabase/RLS、Render 或 Nook 配置。
- 手机热点是当前已验证网络；校园 PEAP、Render Free 长期冷启动表现和正式刷新周期留待后续。当前测试刷新间隔仍为 300 秒，Auto-Deploy 为 Off。
- 本 checkpoint 不记录任何设备凭据、服务器 secret、完整签名 URL 或用户实际待办正文。

## Session: 2026-09-02 — Stage 2B-2 checkpoint and PR preparation

- 恢复 `codex/stage-2b2-local` worktree；未提交范围与上一轮本地交付一致，尚未 push/deploy。
- 本轮将从最新 origin/main 做祖先/差异审计，重跑全部验收后仅 push 独立分支并准备 PR；Stage 2B-2 状态保持 LOCAL IMPLEMENTATION ONLY。
- Fetch 后 `origin/main` 仍为 `a4b4a74`，与当前 HEAD/merge-base 相同；可安全创建单一后代 commit，不需 rebase/merge/force。
- 提交前验收通过：compile、48/48 unittest、diff check、Stage 1 runtime 13/13、Stage 2B-1 校准资产/固定 endpoint/设备认证、字体集合/OFL、`.env`/secret/cache 扫描均通过。
- staged PR diff 通过 23/23 allowlist：13 新增、10 修改、零删除；无 Stage 1/SQL/browser config 路径，无 unstaged 遗漏，`sb_secret_` 仅两个明确 placeholder。
- 已创建单一 `feat: add stage 2B-2 dynamic todo rendering` commit；下一步仅 push 独立分支并核对 PR diff，不 push/merge main。

## Session: 2026-09-01 — Stage 2B-2 local implementation

- 从正式 `origin/main@a4b4a74` 创建隔离本地分支/worktree；本轮不 push。
- 已复核 Stage 2B-1 config/routes/app/tests：固定图、设备认证、300 秒刷新和 800×600 方向基线保持不变。
- 下一步：确认 Supabase 新版 secret header 与官方字体资产后，开始本地代码实现。
- 已确认新版 server secret 使用 `apikey` header，不作为 Bearer JWT；官方 Noto CJK SC Regular + OFL 1.1 来源已定位。
- 已加入官方 Regular 字体与 OFL 1.1；完成 NormalizedContent、TodoProvider、动态 renderer、HMAC signed URL、双版本线程安全 cache、DisplayService 和 API/config 组装。
- `/screen/test.png` 保留；正式 `/screen/current.png` 使用短期 capability URL，失败响应不包含正文或 secret。
- 首轮测试定位并修正空 cache 依赖注入的 truthiness bug；Pillow mode `1` 测试兼容内存 0/1 与重开 PNG 0/255 两种二值表示。
- 最终 48 项 unittest 全部通过；增加真实 bundled font + renderer + FastAPI signed endpoint 集成测试。
- Python compile、`git diff --check`、secret/.env 扫描通过；Stage 1 runtime 13/13 与 `a4b4a74` 一致，Stage 2B-1 校准 generator/PNG 不变。
- Stage 2B-2 保持 **LOCAL IMPLEMENTATION ONLY**：未设置 Render env、未部署、未连接真实 Supabase、未操作 Nook。

## Session: 2026-09-01 — Stage 2B-1 实机验收 checkpoint

- **Stage 2B-1：COMPLETED / VERIFIED。** Nook BYOS 最小显示闭环已通过公网与 Nook Simple Touch BNRV300 实机验收；Stage 2B-2 尚未开始。
- 已验证 Phoenix Project Phase 4 / FW 1.2.2、TRMNL Nook Client v0.16.0、Self-Hosted / BYOS 与 Render Free Web Service（Singapore）的完整链路。
- Render 当前可用；公网 `/health`、`/screen/test.png` 正常，`/api/display` 认证和响应成功。
- Nook 通过手机热点成功联网，下载并显示 800×600 预旋转 PNG；客户端旋转后得到正确的 600×800 竖屏结果。
- 四角方向、双边框、裁切和中文“测试成功”均实机通过；当前刷新测试值为 300 秒。
- 尚未验证校园网 PEAP，以及 Render Free 冷启动和长期运行表现。
- 本轮范围仅为文档记录、secret 检查与 Git checkpoint；不修改任何运行时代码或外部配置。

## Session: 2026-08-31 — GitHub remote reconciliation

- 已获得明确 remote URL；开始执行 add/fetch、main/master 历史与远端 Stage 1 runtime 核对。
- 安全约束：不 force push、不删除远端分支、不修改 Stage 1/Auth/Supabase、不进入 Koyeb 或 Stage 2B-2。
- Fetch 结果：远端默认 `main`，无 `master`；本地 master 与 origin/main 无共同祖先且根目录布局不同，因此停止任何 merge/push，仅继续只读差异核对。
- 远端 main 的 13 个 Stage 1 runtime 文件与本地 checkpoint 对应 blob 全部一致；远端无 server，未发现业务冲突。
- 本轮未 merge、未 push、未 force、未删分支。等待用户确认“基于 origin/main 新建映射集成分支并先走 PR”的安全方案。
- 用户已确认该方案；切换前先将三份 planning 文档提交为本地 master 的独立可追踪 checkpoint。
- Planning checkpoint `2ddad94` 已创建；独立 worktree/branch 已从 `origin/main@66c8ff2` 建立，并完成 server/ 与四份文档的根目录映射，等待验证后提交。
- 会话中断后复核文件仍完整；沙箱读取 worktree 遇到 ownership 保护，后续仅使用宿主权限执行该 worktree 的 Git 检查，不改全局配置。
- 首轮验证中 ancestor、server 12 文件集合、无外层目录、compile 和 unittest 5/5 通过；runtime hash 因从 server workdir 解析了错误相对路径而作废，改从 worktree 根重跑。
- 根目录重跑确认 runtime 13/13 blob 不变；secret 仅占位值，compile/unittest 通过，缓存均 ignored。下一步为暂存并检查相对 origin/main 的完整 diff。
- staged diff 检查通过：16 个新增文件仅限 server/ 与四份文档，无删除、无 runtime 变化、无目录层级错误，diff check 通过。

## Session: 2026-08-31 — Stage 2B-1 checkpoint/push/Koyeb preflight

### Closeout status
- Stage 2B-1 本地实现完成，最终 compile、unittest 5/5、diff/secret/Stage 1 保护检查通过。
- 本地 checkpoint 已创建；当前父 Git 仓库没有 remote，push 因 `No configured push destination` 阻塞，等待 GitHub repository URL。
- 下一步为完成 GitHub push 后进行 Koyeb 公网部署与 Nook 实机 BYOS 测试。
- Stage 2B-2 尚未开始。

## Session: 2026-08-31 — Stage 2B-1

### Phase 1: 协议、现状与部署资料核对
- **Status:** complete
- Actions taken:
  - 完整读取 Stage 2B-1 要求并恢复项目规划。
  - Stage 1C-B preflight 通过并建立 checkpoint `becdc39`。
  - 查阅 TRMNL Nook、Terminus、firmware 和 BYOS 公开资料，获得协议初步线索。
  - 对照官方 tag v0.16.0 精确确认 URL 拼接、headers、JSON parser、图片下载 header 与 800x600 旋转逻辑。
  - 核对 Koyeb、Render、Railway 官方 FastAPI、HTTPS、免费/低成本与休眠限制资料。
- Errors:
  - 沙箱内 `git ls-remote` 因 Schannel 无凭据失败；未改动项目，准备以只读提升权限重试。
  - v0.16.0 clone 成功，但首轮 `rg` workdir 指向项目；改在临时 clone 路径重跑。
  - 按 Gradle 目录猜测源码路径失败；定位后使用仓库实际 Ant `src/com/bpmct/...` 路径完成核对。

### Phase 2: 最小架构与认证设计
- **Status:** complete
- Actions taken:
  - 确定 `server/api`、`server/renderer`、`server/static` 的轻量边界，不创建未使用的 provider/plugin 系统。
  - 确定仅 `/api/display` 校验 `ID` + `access-token`；固定测试图按客户端行为公开。
  - 确定先排版预期 600x800 竖图，再逆时针预旋转为 800x600 源 PNG。

### Phase 3: 实现
- **Status:** complete
- Actions taken:
  - 新增 FastAPI app、环境配置、BYOS routes、固定校准图 generator、PNG、依赖与 server README。
  - 实现 `/health`、受认证 `/api/display`、公开 `/screen/test.png`。
  - 增加 5 个基于 unittest/TestClient 的最小自动测试。
  - 更新项目 README 与三份 planning 文件；未修改既有网页/Auth/Supabase 业务文件。

### Phase 4: 本地测试与保护复核
- **Status:** complete
- Actions taken:
  - 项目本地 `.venv` 安装锁定依赖，固定图生成成功。
  - unittest 5/5 通过：health、正确认证、错误 key、错误 device ID、PNG 类型/尺寸。
  - 真实 Uvicorn + curl：health 200、display 200、错误 key 401、PNG GET 200/image/png。
- Errors:
  - 沙箱网络阻止 pip 下载，获批后仅在项目 `.venv` 安装依赖。
  - 对 PNG 使用 HEAD 得到 405；验收要求是 GET，随后以真实 GET 验证 200 与 `image/png`。未扩大 API 范围。
  - 最终从项目根误用 `.venv` 路径，随后从根运行测试又不符合文档中的 server workdir；进入 `server/` 后最终重跑 5/5 通过。

### Phase 5: 交付与实机边界
- **Status:** complete
- Actions taken:
  - server README 已给出本地启动、环境变量、测试、Easy Setup 和三种部署候选。
  - 明确未执行外部部署，未填写真实凭据，未进入 Stage 2B-2。
  - 公网可达性、旧 Android TLS、物理方向和裁切等待用户在 Nook 上验收。

### Pending User Action
- 完成公网部署后，在 Nook Easy Setup 填写 Base URL、MAC 和 Device API Key 并实机验证方向/裁切。

## Session: 2026-08-26 — Stage 1C-B

### Phase 1: Checkpoint、范围与官方核对
- **Status:** complete
- Actions taken:
  - 完整阅读 Stage 1C-B 要求，用户确认 Stage 1C-A 已真实验收。
  - 项目安全扫描未发现 secret、连接串、配置邮箱或硬编码 token。
  - 建立 `e55a12c chore: checkpoint verified stage 1C-A`。
  - 确认 Git root 位于父 workspace，不适合直接作为独立项目 remote。
  - 核对 Cloudflare Pages private Git 集成、静态 build 和 index 要求。

### Phase 2: 规划与部署设计
- **Status:** complete
- Actions taken:
  - 确定 index 仅跳 login，独立 repo 以项目内容为根。
  - 确定 Pages 配置与新版二手电子阅读器优先路线。

### Phase 3: 最小实现与文档更新
- **Status:** complete
- Actions taken:
  - 新增根入口 `index.html`，仅相对跳转 login。
  - README 更新 private GitHub / Cloudflare Pages 配置和公网验收步骤。
  - 更新 Stage 2A/2B/2C 二手电子阅读器优先路线并保留 ESP32 fallback。
  - 未修改 Auth、数据访问、SQL 或 screen_state 模型。

### Phase 4: 部署兼容与安全静态测试
- **Status:** complete
- Actions taken:
  - 8 个现有 JS 文件通过语法检查。
  - 验证 index 相对跳 login 且没有 Auth 业务逻辑。
  - 验证所有页面资源使用部署兼容相对路径。
  - 对比 `e55a12c`，确认已验收业务文件与数据模型零变化。
  - 扫描 runtime 本地地址/绝对路径及全项目凭据，均通过。
  - 验证本轮最小差异边界与 `git diff --check`。
- Error noted:
  - 相对路径测试脚本的 `$html:` 字符串插值产生 ParserError；项目未执行到该断言，改用 `${html}` 重跑。

### Pending User Action
- 后续创建独立 private GitHub repository 并只发布项目内容。
- 在 Cloudflare Pages 仅授权目标 repo，完成 Git integration 部署和公网验收。

## Session: 2026-08-26 — Stage 1C-A

### Phase 1: Checkpoint、需求与官方核对
- **Status:** complete
- Actions taken:
  - 恢复规划上下文并完整读取 Stage 1C-A 要求。
  - 用户确认 Stage 1B 已真实联网验收。
  - 提交前扫描配置，未发现 secret/service-role/数据库连接串。
  - 仅提交项目并建立 `0673d8d chore: checkpoint verified stage 1B`。
  - 核对 Supabase 官方 Auth、session、signOut 和关闭 signup 文档。

### Phase 2: 架构设计与规划记录
- **Status:** complete
- Actions taken:
  - 确定唯一 client、auth-store、auth-guard、screen-store 的职责边界。
  - 确定 login next 白名单、session 持久化和本地退出行为。
  - 确定 anon 零权限、authenticated 最小权限的 migration/setup 模型。
  - 复核现有 HTML/JS/CSS/SQL，定位 client 初始化、即时数据加载和 anon policy 修改点。

### Phase 3: 实现
- **Status:** complete
- Actions taken:
  - 新增唯一 Supabase client、auth-store、auth-guard 与登录页。
  - editor/display 改为 guard 成功后才初始化；editor 增加本地 session 退出。
  - screen-store 只保留数据 query 并复用共享 client。
  - 新增 Stage 1B→1C-A migration，setup 同步为 authenticated 最小权限。
  - 更新 README、过时 editor 文案与少量登录/隐藏/退出样式。

### Phase 4: 静态测试与安全复核
- **Status:** complete
- Actions taken:
  - 7 个 JS 文件通过语法检查。
  - 验证唯一 client、secret 拒绝、next 白名单和未登录 redirect。
  - 验证 query/Auth API 分层及所有 HTML 加载顺序。
  - 模拟未登录 editor/display，确认不读取数据、不启动 polling。
  - 扫描前端凭据、signUp 和越界功能。
  - 完整断言两份 SQL 的 authenticated-only 最小权限。
- Error noted:
  - 越界扫描无匹配的 `rg` exit 1 被工具视为失败；改用显式条件包装后重跑。

### Pending User Action
- 在 Dashboard 手工创建 Auth 用户且不把密码写入项目。
- 关闭 Allow new users to sign up。
- 执行 `supabase/stage-1c-auth.sql`。
- 用真实账号完成未登录/登录/退出及数据库防线验收。

## Session: 2026-08-26 — Stage 1B

### Phase 1: Checkpoint、需求与资料核对
- **Status:** complete
- Actions taken:
  - 运行 session catchup，完整阅读用户附带要求及三份规划文件。
  - 确认父仓库无其他未提交文件，仅提交 `dorm-todo-screen/`。
  - 建立 checkpoint `b1facde chore: checkpoint verified stage 1A`。
  - 查阅 Supabase 官方 CDN、publishable/secret key、RLS 与 grants 文档。

### Phase 2: Stage 1B 设计
- **Status:** complete
- Actions taken:
  - 确定全局 `screenStore` 的两个异步接口和脚本加载顺序。
  - 确定数据库 trigger、最小列权限、main 行 policies 与 10 秒 polling。
  - 确定配置缺失和网络失败 UI 行为。

### Phase 3: 实现
- **Status:** complete
- Actions taken:
  - 新增 Supabase 配置与统一 screen-store 数据层。
  - editor 改为云端初始加载、异步保存及 loading/success/error 状态。
  - display 改为首次云端加载、10 秒 polling、去重渲染和错误保留旧内容。
  - 新增数据库 setup SQL，并将 README 更新为 Stage 1B。

### Phase 4: 静态测试与安全复核
- **Status:** complete
- Actions taken:
  - 四个 JavaScript 文件通过 `node --check`。
  - 运行架构断言：query 只在 screen-store、无 localStorage、maxlength 单一来源、polling 为 10 秒。
  - 运行占位配置错误路径，确认显示“请先配置 Supabase”。
  - 完整复核 setup SQL 的最小 grants、RLS policies、trigger 与禁止 INSERT/DELETE。
  - `git diff --check` 通过；范围扫描未发现后续阶段实现。

### Pending User Action
- 在 Supabase 创建项目并执行 `supabase/setup.sql`。
- 将 Project URL 与 publishable key 填入 `supabase-config.js`。
- 完成真实跨浏览器/设备联网验收。

## Session: 2026-08-26

### Phase 1: 需求与现状检查
- **Status:** complete
- Actions taken:
  - 运行 planning-with-files session catchup。
  - 检查 workspace 文件清单及 git 状态。
  - 阅读规划模板并整理 Stage 1A 范围。
- Files created/modified:
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 2: 项目结构与设计
- **Status:** complete
- Actions taken:
  - 确定六个交付文件与两个 localStorage key。
  - 创建基础项目结构。
- Files created/modified:
  - `editor.html`、`display.html`、`styles.css`
  - `editor.js`、`display.js`、`README.md`

### Phase 3: 实现
- **Status:** complete
- Actions taken:
  - 实现 300 字输入、实时计数、回填、保存和成功状态。
  - 实现电子纸显示、空状态、更新时间和 storage 事件自动刷新。
  - 添加手机响应式布局和 Live Server 使用文档。

### Phase 4: 测试与验证
- **Status:** complete
- Actions taken:
  - 对两个 JavaScript 文件运行 `node --check`，均通过。
  - 运行项目结构与关键需求断言，全部通过。
  - 运行 `git diff --check` 与越界功能扫描，未发现问题。

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| JavaScript 语法 | 两个脚本 | 无语法错误 | `node --check` 均为 exit 0 | ✓ |
| 项目结构 | 六个交付文件 | 文件齐全 | 断言通过 | ✓ |
| 输入约束 | maxlength / 计数逻辑 | 300 字并实时计数 | 静态断言通过 | ✓ |
| 存储同步 | 两 key / storage 监听 | 写入、读取、跨标签页重绘 | 静态断言通过 | ✓ |
| 换行与溢出 | CSS 规则 | 保留换行且不横溢 | 静态断言通过 | ✓ |
| 范围控制 | 代码扫描 | 无框架、网络与硬件代码 | 扫描通过 | ✓ |
| Stage 1B JS 语法 | 4 个脚本 | 无语法错误 | `node --check` 全部通过 | ✓ |
| 配置占位错误 | 未填写 URL/key | 明确提示且不假成功 | 返回“请先配置 Supabase” | ✓ |
| 数据层隔离 | editor/display | UI 无 Supabase query | `.from()` 仅在 screen-store | ✓ |
| 正式数据源 | 运行时代码 | 无 localStorage | 检查通过 | ✓ |
| Polling/保留 | display 代码 | 10 秒、去重、失败保留旧内容 | 静态复核通过 | ✓ |
| SQL 最小权限 | setup.sql | anon 仅 main SELECT/text UPDATE | 完整断言通过 | ✓ |
| 真实联网 | 真实 project | 跨客户端云同步 | 等待用户配置 | 待验收 |
| Stage 1C-A JS 语法 | 7 个脚本 | 无语法错误 | 全部通过 | ✓ |
| 唯一 client | 两次获取 | 仅创建一次 | 运行测试通过 | ✓ |
| next 安全 | 外部 URL / display | editor fallback / 合法跳转 | 运行测试通过 | ✓ |
| 未登录数据隔离 | editor/display guard null | 不 query、不 polling | 模拟测试通过 | ✓ |
| Auth/DB 分层 | UI/store 脚本 | API 各自集中 | 静态断言通过 | ✓ |
| 前端凭据 | 运行时代码 | 无密码/邮箱授权/secret/token/signUp | 扫描通过 | ✓ |
| Stage 1C SQL | setup + migration | anon 零权限，authenticated 最小权限 | 完整断言通过 | ✓ |
| 真实 Auth | Dashboard 用户 | 登录/退出/在线 RLS | 等待用户配置 | 待验收 |
| Stage 1C-B JS 回归 | 8 个现有脚本 | 语法不变且正常 | 全部通过 | ✓ |
| 根入口 | index.html | 相对进入 login，无 Auth 复制 | 断言通过 | ✓ |
| 部署路径 | 4 个 HTML | 站内引用均相对 | 断言通过 | ✓ |
| 业务零变化 | 与 e55a12c 对比 | Auth/data/SQL/CSS 不变 | 对比通过 | ✓ |
| 公网安全扫描 | 全项目/runtime | 无本地依赖和实际 secret | 扫描通过 | ✓ |
| 最小范围 | Stage 1C-B diff | 仅 index/docs/planning | 检查通过 | ✓ |
| 真实 Pages | private GitHub + Cloudflare | pages.dev 公网行为正常 | 尚未部署 | 待验收 |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| - | 无 | - | - |
| 2026-08-26 | Git `.git/index.lock` permission denied | 1 | 提升权限后仅对项目目录提交，checkpoint 成功 |
| 2026-08-26 | apply_patch 同路径操作及上下文冲突 | 1–2 | 拆分补丁并读取准确上下文后更新 |
| 2026-08-26 | 实现补丁再次包含同路径 delete/add | 2 | 拆为新增/修改与独立脚本替换，不再重复批量方式 |
| 2026-08-26 | 占位配置测试被 CDN 缺失错误抢先 | 1 | 调整 screen-store 校验顺序，先报告配置缺失 |
| 2026-08-26 | 无匹配的 rg 检查返回 exit 1 | 1 | 属预期阴性结果；改用显式条件表达检查通过 |
| 2026-08-26 | SQL 复查使用错误工作目录且错误未终止 | 1 | 不计为通过；在项目目录以 ErrorAction Stop 重跑 |
| 2026-08-26 | 越界扫描无匹配的 rg exit 1（重复包装错误） | 1 | 改为显式 PowerShell 条件，复查通过 |
| 2026-08-26 | PowerShell 将相对路径测试 `$html:` 误解析为变量 | 1 | 使用 `${html}` 明确边界，重跑通过 |
| 2026-08-26 | 最终记录补丁重复更新 progress.md | 1 | 拆为独立补丁后成功 |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Stage 1C-B 部署文件 ready，等待 GitHub/Pages 公网验收 |
| Where am I going? | 独立 private repo → Cloudflare Pages → pages.dev 验收 |
| What's the goal? | 安全部署既有私有待办屏并更新硬件路线 |
| What have I learned? | 当前父 Git root 不宜直接发布；独立 repo 应以项目内容为根 |
| What have I done? | Stage 1C-A checkpoint、index、部署文档、路线更新与静态验证完成 |
