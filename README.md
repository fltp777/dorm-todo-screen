# 宿舍电子待办屏

当前阶段是 **Stage 2B-1：Nook BYOS 最小显示闭环**。

已完成并经用户真实验收：

- Stage 1A 本地网页原型：`b1facde`
- Stage 1B Supabase 云同步：`0673d8d`
- Stage 1C-A 邮箱密码登录与私有访问：`e55a12c`
- Stage 1C-B 公网部署准备（随后已由用户完成 GitHub Pages/手机网络实测）：`becdc39`

现有 GitHub Pages editor/display、Supabase Auth/RLS 和手机公网链路保持稳定。本轮新增独立 `server/`，不修改这些前端业务文件，也不读取 Supabase。

## 当前硬件与 Stage 2B-1 架构

- 终端：Nook Simple Touch BNRV300
- 系统：Phoenix Phase 4 / FW 1.2.2
- 客户端：TRMNL Nook client v0.16.0
- 当前目标：Self-Hosted/BYOS API 与固定校准图的实机闭环

```text
GitHub Pages editor
        ↓
     Supabase
  （本阶段暂不使用）

Nook v0.16.0
        ↓  ID + access-token
BYOS GET /api/display
        ↓  image_url
固定 800x600 test image
        ↓  客户端顺时针旋转
预期 600x800 竖屏显示
```

服务端代码、环境变量、本地测试和 Nook Easy Setup 说明见 [`server/README.md`](server/README.md)。Stage 2B-2 才会实现 Supabase text → renderer → Nook；本阶段没有动态文字渲染。

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

- Stage 2B-1（当前）：Nook → BYOS API → 固定测试图。
- Stage 2B-2（后续）：Supabase text → 服务端黑白图片 → Nook。
- Stage 2C（后续）：完善刷新、睡眠、唤醒和长期运行能力。

硬件端不得重新开放 anon SELECT。当前 `/api/display` 使用独立 device ID/API key；固定校准图因 v0.16.0 下载图片时不转发认证 header 而暂时公开。Stage 2B-2 的真实内容图需使用短期签名 URL 或等价保护。

## 数据模型保持不变

```text
screen_state
├── id
├── text
└── updated_at
```

`updated_at` 足够作为未来渲染内容版本。Stage 2B-1 不修改此模型；新增服务只返回固定测试图，不读取 Supabase。
