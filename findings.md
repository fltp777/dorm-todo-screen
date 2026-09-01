# Findings & Decisions — through Stage 2B-1

## Stage 2B-1 Real-device Verification (2026-09-01)

- **Stage 2B-1：COMPLETED / VERIFIED。** Nook BYOS 最小显示闭环已通过公网和 BNRV300 实机验收，Stage 2B-2 尚未开始。
- 实机组合：Nook Simple Touch BNRV300、Phoenix Project Phase 4 / FW 1.2.2、TRMNL Nook Client v0.16.0、Self-Hosted / BYOS。
- Render Free Web Service 部署在 Singapore region，当前服务可用；公网 `/health` 与 `/screen/test.png` 正常，`/api/display` 的 `ID` + `access-token` 认证和响应成功。
- Nook 通过手机热点成功访问 Render、下载并显示测试 PNG；当前刷新测试值为 300 秒。
- 服务端 800×600 预旋转图经客户端旋转后，在 Nook 上正确显示为 600×800 竖屏；TOP LEFT / TOP RIGHT / BOTTOM LEFT / BOTTOM RIGHT 方向正确，双边框完整、无明显裁切，中文“测试成功”正常。
- 校园网 PEAP 尚未测试；Render Free 冷启动和长期运行表现尚未验证。这两项不影响本次最小显示闭环验收结论。
- 本次仅记录用户提供的实机结果，不修改 server API、renderer、测试图、Supabase、Stage 1 网页、Nook 配置或 Render 配置。

## GitHub Remote Reconciliation (2026-08-31)
- 已添加 `origin=https://github.com/fltp777/dorm-todo-screen.git` 并 fetch；远端默认分支为 `main`，最新为 `66c8ff2 Add files via upload`。
- 远端存在 `origin/main`，不存在 `origin/master`；本地 `master` 最新为 `0e6a142 feat: add stage 2B-1 BYOS test server`。
- `git merge-base master origin/main` 无结果：两条历史完全不相关，不能 fast-forward，也不应直接创建 unrelated-history merge。
- 路径布局不同：本地 Git 根是父 workspace，项目树位于 `dorm-todo-screen/`；远端 Stage 1 runtime 位于 repository 根。直接把本地 master 推到 main 不仅非 fast-forward，还会改变站点根布局。
- 根据用户停止条件，当前结论是禁止 push；仅继续核对远端 Stage 1 文件的实际完整性与 blob 差异，为下一步安全方案提供证据。
- 修正 PowerShell 变量边界后，远端 main 的 13 个 Stage 1 runtime 文件全部存在；每个文件的 Git blob hash 均与本地 `0e6a142:dorm-todo-screen/<path>` 完全相同，包括 login/editor/display、Auth、screen-store、Supabase client/config 与 styles/index。
- origin/main 只有两次 `Add files via upload` 提交：`0059e88`、`66c8ff2`。当前树同时包含根目录 Stage 1 runtime 和一份内容相同的 `dorm-todo-screen-deploy/` 子目录；无 `server/`。
- 最安全的整合不能是 merge/cherry-pick 本地 master：应在用户确认后从 `origin/main` 创建 `codex/stage-2b1-main-integration`，将 `0e6a142:dorm-todo-screen/` 下的 `server/` 及项目文档映射到远端仓库根，保持 13 个 runtime blob 不变；先 push 新分支并审查 PR，再由 GitHub fast-forward/PR merge 到 main。
- 安全门：集成分支必须满足 `origin/main` 是其祖先、runtime blob 逐一不变、无 `.env`/secret、server 完整、diff 只新增 server/docs；不得使用 `--allow-unrelated-histories`、force push 或把父 workspace 的 `dorm-todo-screen/` 整体目录直接推到 main。
- 用户批准后，三个 planning 文件先在本地 master 提交为 `2ddad94`；随后用独立 worktree 从 `origin/main@66c8ff2` 创建 `codex/stage-2b1-main-integration`，避免切换或污染原 master 工作区。
- 映射复制严格来自 `0e6a142` 已跟踪的 server 文件清单；目标根目前仅新增 `server/` 与 README/task_plan/findings/progress，未修改 Stage 1 runtime 或 `dorm-todo-screen-deploy/`。
- 提交前验证：13/13 Stage 1 runtime 工作树 blob 与 origin/main 完全一致；server 映射集合 12/12；无外层 `dorm-todo-screen/`；origin/main 是 HEAD 祖先。
- 凭据扫描只命中明确占位 MAC `AA:BB:CC:DD:EE:FF`、测试错误 MAC `11:22:33:44:55:66` 和占位 key `replace-with-a-long-random-value`。未发现真实 Nook/Supabase/GitHub/私钥。
- Python compile 与 unittest 5/5 通过。compile 产生的 `__pycache__` 均被 `server/.gitignore` 忽略，未被跟踪；暂存后仍需复核 commit tree。
- 完整 staged diff 相对 origin/main 仅含 16 个新增文件：server 12 个文件与四份文档；无删除、无意外路径、无 Stage 1 runtime diff，`git diff --cached --check` 通过。

## Stage 2B-1 Device State & Scope
- BNRV300 已获得，Phoenix Phase 4 / FW 1.2.2 已刷入。
- TRMNL Nook Simple Touch client v0.16.0 已安装，Easy Setup 的系统设置已完成，等待 Self-Hosted/BYOS API Base URL。
- 本阶段链路严格为 Nook → BYOS `/api/display` → 固定测试图片；Supabase 暂不使用。
- Stage 2B-2 才会接入 Supabase text → renderer → Nook。

## Verified TRMNL/Nook v0.16.0 Protocol Findings
- 已将官方仓库 tag `v0.16.0`（commit `a1a102dc779c8e57d78ea9ae2b33d9b21bb315af`）浅克隆到系统临时目录，仅用于源码核对。
- `ApiPrefs.normalizeBaseUrl()` 会去尾斜杠并确保配置值以 `/api` 结尾；`DisplayActivity` 再拼接 `/display`，因此 Easy Setup 可填写 `https://host.example` 或 `https://host.example/api`，最终均请求 `https://host.example/api/display`。
- API 请求固定发送 `ID` 与 `access-token`；还可能发送非认证遥测 `Percent-Charged` 和 `rssi`。服务端只需校验前两个，允许其余 headers。
- JSON parser 接受缺省 `status`，或 `status` 为 `0`/`200`；实际用于显示的字段是绝对 HTTPS `image_url`，`refresh_rate` 是可选秒数。v0.16.0 不读取 `filename`，但响应可保留该字段以方便诊断和兼容其他 TRMNL 客户端。
- 下载图片时客户端只发送 `User-Agent` 与 `Accept: image/*`，不会转发 `ID`/`access-token`。因此 Stage 2B-1 固定测试图必须公开可读；受保护的是 `/api/display`。未来真实内容图应改为短期签名 URL 或等价机制，不能把长期 API key 放进 URL。
- parser 会把恰好 `800×600` 的图片顺时针旋转为 `600×800` 再显示；官方 portrait 图片 `600×800` 不旋转。本阶段选用 `800×600` 横向校准图，让设备端转换路径可被肉眼验证。
- 客户端图片下载走 HTTPS/TLS 1.2 BouncyCastle 实现并重试一次；公网部署必须提供 Android 2.1 客户端可协商的公开 HTTPS 证书链。
- Sources:
  - https://github.com/usetrmnl/trmnl-nook-simple-touch
  - https://github.com/usetrmnl/terminus/blob/main/doc/api.adoc
  - https://github.com/usetrmnl/trmnl-firmware
  - https://github.com/usetrmnl/byos_fastapi

## Stage 2B-1 Issues
- 沙箱内 `git ls-remote` GitHub 失败：Schannel `SEC_E_NO_CREDENTIALS`；下一步使用获批的只读网络命令核对 v0.16.0。
- 第一次读取克隆源码时误按 Gradle 项目猜测 `app/src/main/java`；仓库实际为 Ant 风格 `src/com/bpmct/trmnl_nook_simple_touch`，定位后已按精确路径核对。

## Stage 2B-1 Deployment Findings (2026-08-31)
- Koyeb：官方支持 Git/FastAPI 和自动 TLS `*.koyeb.app`；每组织一个 free instance，闲置 1 小时后 scale-to-zero。适合作为首个免费实测候选。
- Render：官方 FastAPI 路线和免费 TLS `*.onrender.com` 清晰；free web service 闲置 15 分钟休眠，唤醒约一分钟，对旧 Nook 的超时容忍度可能不利。
- Railway：官方 FastAPI 与生成 HTTPS domain；Free 当前每月 $1 credit，Hobby $5/月并含 $5 usage，适合作为避免长冷启动的低成本 fallback。
- 三者都没有对中国大陆各 ISP 的可达性保证；最终选择必须在实际宿舍 Wi-Fi 测 `/health`、PNG 和 Nook TLS。
- Sources:
  - https://www.koyeb.com/docs/deploy/fastapi
  - https://www.koyeb.com/docs/reference/instances
  - https://www.koyeb.com/docs/reference/edge-network
  - https://render.com/docs/deploy-fastapi
  - https://render.com/docs/free
  - https://render.com/docs/tls
  - https://docs.railway.com/guides/fastapi
  - https://docs.railway.com/networking/public-networking
  - https://docs.railway.com/pricing/plans

## Stage 2B-1 Verification Findings
- Python compileall 通过；unittest 5/5 通过。
- 真实 Uvicorn + curl：`/health` 200；正确凭据 `/api/display` 200；错误 key 401；PNG GET 200 且 `Content-Type: image/png`。
- PNG 为二值 800x600、4427 bytes；客户端顺时针旋转后预期为直立 600x800。图中含双边框、四角标签、中心十字、英文/中文和 source/after-client 尺寸。
- 相对 Stage 1C-B checkpoint `becdc39`，受保护的现有 HTML/CSS/JS/Supabase 文件零变化；server 无 Supabase/动态 provider/真实 secret。

## Koyeb Pre-deployment Check (2026-08-31)
- 若 GitHub repository 根就是 `dorm-todo-screen` 内容，Koyeb Work/Root Directory 填 `server`；若推送的是当前父仓库，则必须填 `dorm-todo-screen/server`。当前本地父 Git 仓库没有 remote，尚不能确认 GitHub 实际采用哪种布局。
- Builder：Buildpack；Build Command 推荐留空。Koyeb 会因 workdir 根的 `requirements.txt` 检测 Python 并自动安装依赖，而自定义 Build Command 是自动构建后的附加命令，重复填写 `pip install` 没有必要。
- Run/Start Command：`uvicorn app:app --host 0.0.0.0 --port $PORT`；Health Check Path：`/health`；route 使用根 `/`，不要把 Koyeb route 配成 `/api`（子路径 route 会剥离 prefix）。
- `requirements.txt` 位于 server workdir 根，`app.py` 也位于同一目录，当前 requirements 和 import/start 路径适合 Koyeb buildpack。
- 部署前即可生成并填写 `NOOK_DEVICE_ID`、`NOOK_API_KEY`、`REFRESH_RATE_SECONDS=300`；`PUBLIC_BASE_URL` 必须等 Koyeb 分配 `https://*.koyeb.app` 后确定。
- 不存在启动鸡生蛋：`PUBLIC_BASE_URL` 是可选值，缺失时服务可启动并由 request origin 生成 URL。最稳妥流程是先不填该变量完成第一次部署，取得 HTTPS URL 后立刻添加 `PUBLIC_BASE_URL=https://...koyeb.app` 并触发一次配置 redeploy，再测 `/api/display`。
- Free Instance 无流量 1 小时后 scale-to-zero。300 秒轮询在 Nook 持续运行期间理论上足以保持实例活跃；设备睡眠/断网超过 1 小时后首个请求会承担冷启动，可能触发 Nook 超时/重试，必须实测。
- `*.koyeb.app` 自动 TLS 只证明平台端提供 HTTPS；Android 2.1 + 客户端内置 BouncyCastle 对实际证书链/SNI/握手的兼容性仍必须用 BNRV300 实测。
- Official sources:
  - https://www.koyeb.com/docs/deploy/fastapi
  - https://www.koyeb.com/docs/build-and-deploy/deploy-with-git
  - https://www.koyeb.com/docs/reference/instances
  - https://www.koyeb.com/docs/reference/edge-network

## Stage 1C-B Deployment & Hardware Decisions
- Stage 1C-A 已由用户真实验收；checkpoint 为 `e55a12c`。
- 本轮只做公网静态部署准备，不实际连接 GitHub/Cloudflare，也不修改已验收 Auth、数据访问或 RLS。
- 新增 `index.html` 只负责相对跳转 `login.html`；login 继续根据现有 session 进入 editor。
- 当前 Git root 是项目父级 workspace `云端备忘录/`，不是 `dorm-todo-screen/`；不得直接把父 repo 推到独立项目 remote。
- 推荐的独立 private GitHub repo 应让 `dorm-todo-screen` 内容直接位于 repo root；Pages Root directory 留空、Build command 留空、Build output directory 为 `.`。
- Cloudflare Pages Git integration 支持 private GitHub repo；GitHub App 应只授权目标仓库。
- 官方文档说明无框架时 Build command 可留空；静态 HTML 顶层需有 index.html 避免根路径 404。
- Sources:
  - https://developers.cloudflare.com/pages/get-started/git-integration/
  - https://developers.cloudflare.com/pages/configuration/build-configuration/
  - https://developers.cloudflare.com/pages/framework-guides/deploy-anything/
  - https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/

## Updated Hardware Route
- 首选：手机网页 → Supabase → 服务端 text/updated_at 转黑白图片 → 受保护只读 endpoint → 可联网二手电子阅读器全屏显示。
- 候选包括 Kindle、Nook Simple Touch、Kobo 或其他可运行自定义脚本并全屏显示图片的设备；型号尚未确定。
- Stage 2A：选择并验证 Wi-Fi、root/jailbreak/shell、全屏图片能力。
- Stage 2B：实现服务器端 text → 黑白图片。
- Stage 2C：实现阅读器版本检查、下载、全屏刷新、睡眠/定时唤醒。
- fallback：找不到合适二手阅读器时，再评估 ESP32 + e-paper。
- 不为硬件重新开放 anon SELECT；未来使用独立只读 device token / protected endpoint，待设备确定后设计。
- `screen_state` 保持 `id/text/updated_at`，本轮不增加 image/device/render 字段。

## Stage 1C-B Verification Findings
- 所有 8 个现有 JavaScript 文件通过 `node --check`。
- `index.html` 同时包含相对 meta refresh 和 login fallback link，不复制 Auth 逻辑。
- 四个 HTML 的站内资源/页面引用均为部署兼容相对路径；唯一外部脚本为 HTTPS jsDelivr CDN。
- 运行时代码无 localhost、127.0.0.1、Windows 绝对路径或 file URL。
- 相对 Stage 1C-A checkpoint，Auth、screen-store、HTML 业务页、CSS、SQL 和数据模型零差异。
- 本轮差异严格限制为 `index.html`、README 和三份 planning 文件。
- 全项目扫描未发现实际 secret、数据库连接串、配置邮箱或硬编码 token。
- `git diff --check` 通过；尚未真实 push GitHub、连接 Cloudflare 或访问 pages.dev。

## Stage 1C-A Requirements & Architecture
- Stage 1A 和 Stage 1B 均已由用户真实验收；Stage 1B checkpoint 为 `0673d8d`。
- 手机端最终继续使用网页，不要求改为微信小程序。
- Supabase Auth 使用 Email + Password；不提供 signUp、Magic Link、OAuth 或公开注册。
- editor 和 display 均须在认证检查成功后才初始化并读取数据。
- `supabase-client.js` 创建唯一 client；`auth-store.js` 集中 Auth API；`screen-store.js` 集中数据库 query。
- anon 不应拥有 screen_state 的任何数据权限；所有由项目所有者显式创建的 authenticated 用户共享 main 行，不做按用户隔离。
- 用户需在 Dashboard 手工创建私人用户并关闭 “Allow new users to sign up”。
- future ESP32 不得重新开放 anon SELECT；Stage 2 应设计独立只读设备认证/API，例如 device token 获取渲染图片。
- 中文最终仍由服务器转为黑白图片，ESP32 只负责下载显示；不属于本轮。

## Stage 1C-A Existing Code Findings
- Stage 1B 的配置校验、secret/service-role 检测和 client 缓存当前位于 `screen-store.js`，应原样迁移到共享 client 模块。
- editor/display 当前在脚本末尾立即加载 screen 数据，必须改为异步 bootstrap：guard 成功后才调用数据层。
- 现有 HTML 未设置 auth-pending；需要在 body 初始隐藏业务 main，认证成功再 reveal，避免内容闪现。
- editor 页底部已有低调显示页链接，可并列加入低调退出按钮；display 不增加操作控件。
- Stage 1B setup.sql 仍给 anon SELECT/UPDATE，必须同时更新最新版 setup 并提供现有项目 migration。

## Supabase Auth Official Findings (2026-08-26)
- `supabase.auth.signInWithPassword({ email, password })` 用于邮箱密码登录；本项目不调用 signUp。
- 浏览器 Supabase client 默认 `persistSession: true`，SDK 自行管理 session 存储与刷新，不应自建 token key。
- `getSession()` 可读取/必要时刷新浏览器 session；真正数据安全仍由 authenticated grants + RLS 提供。
- `onAuthStateChange` 可监听 INITIAL_SESSION、SIGNED_IN、SIGNED_OUT、TOKEN_REFRESHED 等事件。
- `signOut({ scope: "local" })` 退出当前浏览器 session；默认 scope 是 global，因此本项目显式指定 local。
- 官方 General configuration 说明关闭 “Allow new users to sign up” 后仅既有用户可登录。
- Sources:
  - https://supabase.com/docs/reference/javascript/auth
  - https://supabase.com/docs/reference/javascript/auth-getsession
  - https://supabase.com/docs/reference/javascript/auth-onauthstatechange
  - https://supabase.com/docs/reference/javascript/auth-signout
  - https://supabase.com/docs/guides/auth/general-configuration

## Stage 1B Requirements & Architecture
- Supabase 已确定为 Stage 1B 云端数据源；UI 保持 Stage 1A 已验收设计。
- 数据流固定为 `editor/display → screen-store → Supabase`，查询不得散落在 UI 脚本。
- `screen-store.js` 统一提供 `loadScreen()` 和 `saveScreen(text)`。
- display 使用 10 秒 polling，不使用 Realtime；请求失败时保留最后成功内容。
- localStorage 的两个 Stage 1A key 停止使用，不设置双数据源或失败回退。
- 中文最终方案是服务器排版并转黑白图片，ESP32 只显示图片；不属于本轮实现。
- 无登录的 publishable key + anon UPDATE 是临时个人原型模型，不是正式公网写权限方案。

## Supabase Official Documentation Findings (2026-08-26)
- 官方浏览器 CDN：`https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2`。
- publishable key 用于公开客户端；未登录时数据库角色为 `anon`，key 本身不是数据保密机制。
- secret key / legacy service_role 会绕过 RLS，绝不能进入浏览器代码或版本库。
- grants 决定角色能否执行操作，RLS policy 决定操作可涉及哪些行，两者都必须配置。
- 官方建议先启用 RLS、撤销客户端角色既有权限，再仅授予所需权限。
- UPDATE policy 应包含 `using` 与 `with check`，且 UPDATE 正常工作需要对应 SELECT policy。
- Sources:
  - https://supabase.com/docs/reference/javascript/installing
  - https://supabase.com/docs/guides/database/postgres/row-level-security
  - https://supabase.com/docs/guides/getting-started/api-keys
  - https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys

## Requirements
- 两个独立页面：`editor.html` 编辑，`display.html` 只显示。
- textarea 最多 300 字，实时计数，允许保存空字符串，重开时回填。
- 点击“更新屏幕”写入正文和当前时间，并短暂显示“✓ 已更新”。
- display 保留换行、自动换行、显示低调更新时间；从未保存时显示“暂无内容”。
- 使用 `localStorage` 持久化，使用 `storage` 事件跨标签页自动刷新。
- 页面有 viewport meta、基础响应式布局、系统字体和简洁电子纸视觉。
- README 说明 Stage 1A、Live Server 启动及验收方法。

## Workspace Findings
- 2026-08-26 初检时 workspace 无普通项目文件，`git status --short` 无输出。
- workspace 文件夹名为“云端备忘录”，因此按要求创建 `dorm-todo-screen/`。
- session-catchup 未报告未同步上下文。

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 原生脚本使用 `defer` | 保证 DOM 解析后执行且代码简单 |
| 时间保存为 ISO 字符串 | 可持久化、可可靠解析，display 再格式化为本地 HH:mm |
| 用 `textContent` 渲染正文 | 正确显示用户文字且避免将输入解释为 HTML |
| CSS `white-space: pre-wrap` + `overflow-wrap: anywhere` | 保留换行并防止长连续文本横向溢出 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| 无 | - |
| 沙箱无法写父仓库 `.git/index.lock` | 提升权限后只暂存并提交项目目录，checkpoint 为 `b1facde` |
| 规划补丁操作/上下文冲突 | 拆为更小的定点补丁，并先读取准确文件内容 |

## Verification Findings
- `node --check` 已确认 `editor.js` 与 `display.js` 无 JavaScript 语法错误。
- 结构断言已确认 viewport、300 字限制、关键 DOM 元素、固定 localStorage key、storage 监听和换行样式存在。
- `git diff --check` 通过；范围扫描未发现框架、网络请求或后续阶段实现。
- 最终跨标签页行为需在用户本机同源 Live Server 页面中完成浏览器验收。

## Stage 1B Verification Findings
- `editor.js`、`display.js`、`screen-store.js`、`supabase-config.js` 均通过 `node --check`。
- 占位配置运行检查确认 `loadScreen()` 明确返回“请先配置 Supabase”，不会静默或回退 localStorage。
- UI 脚本不包含 `.from()` 查询；全部 Supabase 查询仅位于 `screen-store.js`。
- 所有运行时代码均不再引用 localStorage 或 Stage 1A 两个 key。
- display 以 10 秒间隔 polling，通过状态签名避免无变化时重绘，成功显示后失败保持旧 DOM。
- SQL 复核确认：main seed、300 字约束、数据库时间 trigger、RLS、撤权、anon SELECT、text 列 UPDATE、main 行 SELECT/UPDATE policies 均存在。
- SQL 没有 anon INSERT/DELETE grant 或 policy；trigger function 对 public/anon/authenticated 的默认 execute 也已撤销。
- 未提供真实 Project URL/key，未执行真实 Supabase 网络链路测试。

## Stage 1C-A Verification Findings
- 7 个 JavaScript 文件均通过 `node --check`。
- 共享 client 运行测试确认只创建一次，并拒绝明显 `sb_secret_` key。
- auth guard 运行测试确认外部 URL next 被降级为 editor，display next 正确跳登录。
- editor/display/login 无数据库 query；query 只在 screen-store。screen/login/editor/display 无直接 Auth API；Auth 调用只在 auth-store。
- HTML 脚本加载顺序、email/password input、密码管理器 autocomplete、form submit 和 auth-pending 均通过断言。
- 未登录控制流模拟确认 editor 不读取 screen，display 不读取也不启动 polling。
- 前端扫描未发现 signUp、硬编码邮箱、实际 secret、数据库 URL 或硬编码 token。
- setup.sql 与 stage-1c-auth.sql 均确认：anon 无 grant/policy；authenticated 仅 SELECT + UPDATE(text)，policy 只允许 main，无 INSERT/DELETE。
- 尚未使用真实邮箱密码执行 Auth 登录、退出及在线 RLS 防线测试。
