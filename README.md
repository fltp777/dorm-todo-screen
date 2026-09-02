# 宿舍电子待办屏

当前状态：**Stage 2B-1：COMPLETED / VERIFIED**；**Stage 2B-2：LOCAL IMPLEMENTATION ONLY**。动态待办服务已完成本地代码与 mock 自动测试，但尚未部署，也未进行真实 editor → Supabase → Render → Nook 验收。

已完成并经用户真实验收：

- Stage 1A 本地网页原型：`b1facde`
- Stage 1B Supabase 云同步：`0673d8d`
- Stage 1C-A 邮箱密码登录与私有访问：`e55a12c`
- Stage 1C-B 公网部署准备（随后已由用户完成 GitHub Pages/手机网络实测）：`becdc39`

现有 GitHub Pages editor/display、Supabase Auth/RLS 和手机公网链路保持稳定。本轮新增独立 `server/`，不修改这些前端业务文件，也不读取 Supabase。

## Stage 2B-1 实机验收结果

- 设备：Nook Simple Touch BNRV300，Phoenix Project Phase 4 / FW 1.2.2。
- 客户端：TRMNL Nook Client v0.16.0，Self-Hosted / BYOS 模式。
- 公网服务：Render Free Web Service，Singapore region；当前服务可用。
- `/health`、`/screen/test.png` 和带 `ID` + `access-token` 认证的 `/api/display` 均已通过公网验证。
- Nook 通过手机热点成功访问 Render、下载并显示测试 PNG；当前刷新测试值为 300 秒。
- 服务端输出 800×600 预旋转图，客户端旋转后在 Nook 上正确显示为 600×800 竖屏。
- 四角方向标记、双边框、裁切和中文“测试成功”均已实机确认正常。
- 校园网 PEAP 尚未测试；Render Free 冷启动及长期运行表现尚未验证。

## Stage 2B-2 本地实现

本地服务现已具备：

- 通过 server-only Supabase secret 只读 `screen_state(id='main')` 的 `text,updated_at`；浏览器 publishable key、Auth 和现有 RLS 不变。
- `TodoProvider` 将数据库行转换为 provider-neutral `NormalizedContent`，renderer 不直接访问 Supabase。
- 使用随项目分发的 Noto Sans CJK SC Regular，将 300 字以内正文排成严格黑白 600×800 portrait，再逆时针预旋转为 800×600 PNG。
- 使用 `updated_at` 派生内容版本；相同版本复用最多两个 artifact 的进程内缓存。
- `/api/display` 继续校验 `ID` + `access-token`，只返回约 900 秒有效的 HMAC-SHA256 签名图片 URL，不返回正文或 server secret。
- `/screen/current.png` 无需 Nook 额外 header，但必须通过 `v`、`exp`、`sig` 验证；Stage 2B-1 `/screen/test.png` 继续保留。

本阶段尚未修改 Render 环境变量、部署新版服务或操作 Nook，因此不能标记为 verified。

## 当前硬件与 Stage 2B-2 本地架构

- 终端：Nook Simple Touch BNRV300
- 系统：Phoenix Phase 4 / FW 1.2.2
- 客户端：TRMNL Nook client v0.16.0
- 当前目标：动态待办图片链路的本地实现与部署前验证

```text
GitHub Pages editor
        ↓
     Supabase
  screen_state.main
        ↓ server-only read
 TodoProvider → NormalizedContent
        ↓
  black/white renderer
        ↓
 800x600 pre-rotated PNG

Nook v0.16.0
        ↓  ID + access-token
BYOS GET /api/display
        ↓  signed image_url
GET /screen/current.png?v=...&exp=...&sig=...
        ↓  客户端顺时针旋转
预期 600x800 竖屏显示
```

服务端代码、环境变量、本地测试和部署前步骤见 [`server/README.md`](server/README.md)。当前只完成本地实现；真实公网与 Nook 验收仍待后续执行。

## 当前网站架构

```text
index.html → login.html
                ↓
          Supabase Auth
                ↓
     authenticated 用户
          ↙           ↘
   editor.html     display.html
          ↘           ↙
          screen-store.js
                ↓
       screen_state.main
```

访问站点根路径 `/` 时，`index.html` 使用相对地址进入 `login.html`。如果浏览器已有有效 session，login 页会按既有逻辑自动进入 editor。

## Supabase 安全边界

前端允许包含 Project URL 和 publishable key，因为它们属于公开客户端配置。真正的数据边界是：

```text
Supabase Auth + PostgreSQL grants + RLS
```

当前权限保持不变：

| 角色 | SELECT main | UPDATE main.text | INSERT | DELETE |
|------|-------------|------------------|--------|--------|
| `anon` | 否 | 否 | 否 | 否 |
| `authenticated` | 是 | 是 | 否 | 否 |

不要在项目中加入 secret/service-role key、数据库密码、用户密码或 session token。公网静态页面的源码和 publishable key 对访问者可见，这是预期行为；未登录用户仍会被数据库权限拒绝。

Stage 2B-2 的 Supabase secret 仅允许作为 Render Environment Variable 存在。它绕过 RLS，因此服务端代码只执行固定的 `main` 行 SELECT，绝不把该 key 放入前端、Nook、URL、日志或 Git。

## 当前 Git 仓库情况

本项目文件夹目前不是 Git repository 根目录；Git root 位于更高一级的父 workspace，其中可能包含其他项目。因此：

**不要把当前父 repository 直接设置为 `dorm-todo-screen` 的 GitHub remote，也不要把整个父 repository 推送到 GitHub。**

推荐做法：

1. 在 GitHub 创建一个空的 private repository，例如 `dorm-todo-screen`。
2. 在当前项目之外创建一个专用本地副本，只复制 `dorm-todo-screen` 文件夹内的内容。
3. 在该专用副本中初始化独立 Git repository。
4. 确认 `git status` 只显示本项目文件。
5. 添加 private GitHub remote，提交并推送到 `main`。

如果希望保留本项目在父仓库中的 checkpoint 历史，可以从父仓库使用 `git subtree split --prefix=dorm-todo-screen` 生成只包含本项目的发布分支，再将该分支推送到新 private repository。执行前应再次检查目标 repository 和待推送分支；本轮没有自动执行这些外部操作。

独立 GitHub repository 的根目录应直接包含：

```text
index.html
login.html
editor.html
display.html
styles.css
...
```

不要让 GitHub repository 再额外嵌套一层 `dorm-todo-screen/`。

## Cloudflare Pages 部署

Cloudflare Pages 可以通过 Git integration 连接 private GitHub repository。建议只授权上一步创建的目标 repository。

1. 登录 Cloudflare Dashboard。
2. 进入 **Workers & Pages**。
3. 选择 **Create application → Pages → Connect to Git**。
4. 连接 GitHub，并只授权 `dorm-todo-screen` private repository。
5. 选择该 repository 和 production branch `main`。
6. 使用以下配置：

| 配置 | 值 |
|------|----|
| Framework preset | `None` |
| Root directory | 留空（repository 根就是网站根） |
| Build command | 留空；如果界面要求命令，可填 `exit 0` |
| Build output directory | `.` |
| Environment variables | 不需要 |

7. 选择 **Save and Deploy**。
8. 部署成功后获得 `https://你的项目.pages.dev`。
9. 访问根地址，确认进入 login；再执行下方公网验收。

如果未来错误地连接了当前父 workspace repository，则 Root directory 必须设为 `dorm-todo-screen`、Build output directory 仍为 `.`。但不推荐这种做法，因为它会把父仓库的其他历史和文件带到 GitHub。

## 公网验收清单

实际部署后测试：

1. 打开 `https://项目.pages.dev/`，确认自动进入登录页。
2. 隐私窗口访问 `editor.html` 和 `display.html`，确认跳登录且不显示屏幕内容。
3. 输入错误密码，确认统一提示“邮箱或密码不正确”。
4. 正确登录后确认 editor 可读取和更新文字。
5. 同一 session 打开 display，确认内容和 polling 正常。
6. 退出后再次访问业务页，确认重新要求登录。
7. 在浏览器开发者工具中确认资源均通过 HTTPS 和相对站内路径加载，无 localhost 请求。
8. 确认未登录的 Data API 请求仍被 Supabase grants/RLS 拒绝。

以上网站公网验收已由用户使用手机 4G/5G 完成；本节保留作为回归清单。

## 已确定的硬件路线

首选方案已从自制 ESP32 墨水屏调整为商品化二手电子阅读器：

```text
手机网页
   ↓
Supabase text + updated_at
   ↓
服务端生成对应尺寸黑白图片
   ↓
受保护的只读图片/API
   ↓ Wi-Fi
二手电子阅读器
   ↓
全屏显示
```

终端已确定为 Nook Simple Touch BNRV300，不再回到 ESP32 方案讨论。

后续阶段：

- Stage 2B-1（已实机验证）：Nook → BYOS API → 固定测试图。
- Stage 2B-2（本地实现完成，待部署/实机验收）：Supabase text → 服务端黑白图片 → Nook。
- Stage 2C（后续）：完善刷新、睡眠、唤醒和长期运行能力。

硬件端不得重新开放 anon SELECT。`/api/display` 使用独立 device ID/API key；固定校准图继续公开用于诊断，真实内容图使用短期 HMAC 签名 URL，因为 v0.16.0 下载图片时不转发认证 header。

## 数据模型保持不变

```text
screen_state
├── id
├── text
└── updated_at
```

`updated_at` 作为动态渲染内容版本，不新增 version/image URL 列。Stage 2B-2 不修改此数据模型、grants 或 RLS。
