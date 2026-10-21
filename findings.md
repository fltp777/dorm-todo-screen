# Findings & Decisions — through Stage 2B-2 verification

## Stage 2C 夜间长睡眠 / 动态 refresh_rate（2026-10-21，Git 收尾中）

- Stage 2C 已由用户报告上线并在 Nook 真机验收；当前 `origin/main` 是 PR #5 merge commit `dce97ee`，包含 `b5263a2` 的 Flow/Yijing 代码。本轮从该 main 新建 `codex/night-sleep`，不把无关历史追加到旧 battery 分支。
- 时间表是业务规则而不是图片内容：Asia/Shanghai 的 `[07:10, 22:40)` 返回现有白天 refresh interval；`>=22:40` 或 `<07:10` 计算到下一次 07:10 的实际秒数。夜间请求仍正常读内容、签图和响应，只改变 response 的 `refresh_rate`。
- 180° 旋转明确暂缓；本轮不得修改 Flow layout、易经、editor、schema、battery/footer、signed URL/cache、Nook/TRMNL 或 Render keepalive。
- `ZoneInfo("Asia/Shanghai")` 在当前 Windows Python 缺少 `tzdata` 时不可用。项目已有的明确 `timezone(timedelta(hours=8), name="Asia/Shanghai")` 不依赖本机 locale 或 IANA 数据库；中国业务时钟没有 DST 转换需求，因此本轮作为等价、可移植实现使用。
- `server/refresh_schedule.py` 的 `compute_refresh_rate(now, daytime_refresh_seconds)` 是纯函数。它在 `[07:10, 22:40)` 返回配置 interval，夜间用 `datetime.combine`/`timedelta` 求下一次 07:10 并向上取整秒数。route 在该函数抛错时仅记录无敏感信息 warning 并回退到配置值，正常图片/签名/缓存仍完成。
- `REFRESH_RATE_SECONDS` 默认值与示例调整为 1800，仍只代表白天 interval；没有新增环境变量或配置系统。API JSON 字段、signed URL 的 `v/b/r/exp/sig`、cache key/上限和 refresh footer 均未修改。
- 收尾前复核的工作树差异仅限 schedule 模块、`/api/display` 的 response 字段计算、1800 默认/示例、对应 API/schedule 测试，以及 README/planning 文档；没有 renderer、签名、cache、Supabase、前端或 cron-job.org 文件变化。

## Stage 2C Right Reminder Gap and Yijing Glyph Width Review（2026-10-02，进行中）

- 当前右栏标题从 `FLOW.content_top_y` 绘制，但正文起点复用了左栏 `_title_end_y(40)`，未使用 `stroke_width=1` 的实际标题 bbox；这使标题与第一条提醒之间仅保留很小的视觉空白。
- 当前卦象宽度由 `TodoRenderer._glyph_width(size, line_count)` 计算：六爻使用 `round(size * 0.72)`，三爻使用 `round(size * 0.62)`，最小 16 px。thickness 为 `max(1, size // 16)`，yin central gap 为 `max(3, width // 4)`，vertical gap 为 `max(1, size // 15)`。
- 首张 `yijing_glyph_width_comparison.png` 的候选符号本身清楚，但顶部完整像素说明横跨相邻列；将改为每列短标签和一行紧凑宽度标注，不影响 production renderer。
- 右栏标题实际 bbox 为 `(415, 33, 577, 75)`；50 px「钥匙」首行 bbox 为 `(416, 91, 516, 139)`，实际黑色像素间距精确为 16 px。body draw y 为 76，最后一条 bbox bottom 为 454，远高于 footer content limit y=730；reminder 字号保持 50 px，项目 line step 仍为 63 px。
- 对比图使用 30 px heading 样本：current 六爻/三爻为 22/19 px，+15% 为 25/22 px，+20% 为 26/23 px，+25% 为 28/24 px。stroke thickness 为 1 px、vertical gap 为 2 px；yin central gap 保持六爻 5 px、三爻 4 px，不随横向放大。+25% 在当前 regular full、single line 与最长整卦 heading 的宽度测试中仍未超过 340 px 左栏边界。
- production renderer 最终固定使用 +20%（`YIJING_GLYPH_WIDTH_SCALE=1.20`）横向 scale；它不改变 shared left font、首行 baseline、纵向几何或文本 wrap。右栏最终标题/第一项实际 bbox 间距固定为 16 px（`REMINDER_TITLE_BODY_GAP=16`）。

## Stage 2C Frozen Layout and Deployment-Readiness Audit（2026-10-20，进行中）

- 用户已确认最终生产参数：`YIJING_GLYPH_WIDTH_SCALE = 1.20` 与 `REMINDER_TITLE_BODY_GAP = 16`；Flow 版式和其余视觉比例从此冻结，后续只接受明确 bug 修复。
- 已将未经改写的正式 JSON 放入当前 worktree 的 `yijing database/yijing_64_hexagrams.json`，并与原始来源 SHA-256 一致。`server/yijing_catalog.py` 现在只解析该 repository-root 相对路径，不再向父目录搜索；这避免本机共享目录掩盖 Render clone 中缺文件的问题。该文件目前尚未被 Git 跟踪，必须在后续人工确认的 commit 中纳入仓库后才会随部署到达 Render。
- 目录审计结果：源 JSON 为 64 卦、每卦 6 常规爻（384），乾「用九」与坤「用六」各一页，flatten 后共 450 页；position 为 0..449。编辑器的上一条/下一条在边界直接返回，没有自动轮换定时器；冻结的 `NormalizedContent` 与 renderer 只读取 position，render 不回写或推进它。
- 用户已人工执行并验证 `supabase/stage-2c-fixed-v2-state.sql`：既有 `public.screen_state.main` 的 `text`/`updated_at` 保留，`daily_reminder_text=''` 与 `yijing_position=0` 正常。该 SQL 只对既有表加 `daily_reminder_text text not null default ''` 与 `yijing_position integer not null default 0`，并加 300 字/0..449 check；不含建表、RLS 或 policy 改动。authenticated 的新增列 UPDATE grant 与既有 authenticated-only 模型一致，未增加 anon 权限。
- refresh footer 取成功 `/api/display` 时的服务端 UTC 时间并在 renderer 转为 UTC+8 `HH:MM`，不使用 Supabase `updated_at`。该 UTC minute 同时进入 display version、签名 URL 的 `r` 参数和 artifact 的 refresh state；cache miss 会按已签名 minute 重建相同图片，cache 上限仍为两个版本。
- 最终 deliverables 为 `server/production_previews/01_final_regular_full_hexagram.png` 至 `05_final_double_pressure.png`：均为 600×800、mode `1`；metadata 显示无 overflow、无 todo/reminder/Yijing truncation。全套 71 unittest、compileall、三个 root JS syntax check 与 `git diff --check` 均通过。
- Git 收尾前已删除旧 fixed-v2 helper、纯实验 preview script 和所有生成 PNG/metadata；它们不属于运行时或正式回归输入。保留 `server/generate_flow_production_previews.py` 作为冻结 Flow 的可再生本地 review 工具，并以 `server/.gitignore` 排除 `layout_previews/`、`production_previews/` 输出。
- 正式 JSON 的工作文件与 source SHA-256 均为 `B606AEAEED14B9CB9AF160B04B59A6BB23876FED12CF245BC9E03A94AF2CBD05`，已进入 staged index；目录统计、71 unittest、compileall、前端 JS syntax 与 staged diff 检查均在 commit 前通过。用户描述的线上 migration 验证结果与 staged SQL 的默认值/约束操作一致；本轮没有再次连接或修改 Supabase。

## Stage 2C Flow Typography Fit Efficiency Audit（2026-10-02）

- Production fit 使用 `left_font_size` 对左栏整体求解；可用范围为 y=22..732，共 710 px，footer 顶线 y=746，保留 14 px 单一安全余量。
- 发现并修正明确的重复预算：`line_step = ink height + leading`，旧预算把每个块的最后一行也计作完整 `line_step`。新增 `line_box_height` / `wrapped_lines_height`，最后一行只计字面高度；段间距仍只在段与段之间计一次，divider 上下各 10 px 只计一次。
- `_draw_limited_lines` 与 `_draw_paragraphs_limited` 改用字面高度做边界判断、仍以 `line_step` 推进行间；因此 measurement 与实际 draw 一致。右栏 fit、geometry、footer、divider 规则不变。
- 修正前五个 shared size 为 28/40/24/24/22；修正后为 30/40/26/24/22。修正后 production preview 仍全部 600×800、1-bit、无 overflow/truncation。
- 与历史 `server/layout_preview.py` 的 36/40/32/32/26 不可直接比较：历史 preview 使用 mock 易经字段（如整卦 8 行、压力页 6/10/9 行），且标题/易经 heading 独立固定 40 px；production 使用正式数据库真实页面（对应 12/4/11/14/12 行）并执行全左栏 shared-size coupling。因此剩余字号差异来自内容量与规则差异，不是额外重复扣高。
- 当前 `S+2` 候选因总高超出 710 px 而拒绝：full hexagram 32→-14 px、long todo 28→-51 px、long Yijing 26→-20 px、double pressure 24→-16 px；single line 的 42 px 虽有 122 px余量，但超过配置最大字号 40，不在候选范围。
- 粗体 stroke_width=1 仅带来约 1 px bbox 扩展，现有 line box 与安全余量足以覆盖；wrap 与 draw 均使用同一字体、宽度和 line step。`layout_preview.py` 仍是历史 local-only helper，不是 production 计算源。

## Stage 2C Flow Layout 与正式易经数据库接线（2026-10-02，进行中）

- 用户已明确把 production 默认从 fixed v2 改为左侧连续 flow layout；fixed-v2 的 y=373 分线不再是正式 renderer 约束。x=392 竖线、y=746 footer、1-bit 600×800 portrait review 输出，以及最终已实机验证的 800×600 预旋转协议仍应保留。
- 用户已在工作区放入正式易经数据库。本轮必须以实际文件/schema、原文（含传统字与标点）和真实顺序构建 sequence；此前仅供接线验证的两页乾卦 mock catalog 不得继续作为 production 数据源。
- 用户要求 footer 左侧显示经认证的本次 `/api/display` 成功响应时间（Asia/Shanghai），而非 Supabase `updated_at`。若这要求 artifact 重新渲染，必须采用有界 cache，且在实现与测试后明确说明最小 version/signed URL 改动。
- 正式数据库文件为共享工作区 `yijing database/yijing_64_hexagrams.json`（137,592 bytes）；顶层实际为 `hexagrams` 64 条、命名 `trigrams` dict 和 source metadata。每卦 6 条 regular lines，只有 #1 乾有用九、#2 坤有用六；展平后为 64 + 384 + 2 = 450 页。服务器的 path resolver 先找 checkout 根目录，再兼容当前 managed-worktree 的共享父目录；未来部署前 JSON 必须放进 repository-visible 的同名根目录。
- flow 正式 renderer 只保留 x=392 竖线与 y=746 footer；它从最终待办行高计算 divider。旧 `renderer/fixed_v2_layout.py` 仍是未提交的历史 preview/local 文件，但不被 production `TodoRenderer` 导入。
- refresh footer 采用 UTC minute state `r`：每次认证成功 `/api/display` 的 UTC minute 同 content version、电量 `b` 一起 hash，并包含在 HMAC canonical data。最多两项 artifact cache 仍有界；图片端 cache miss 可借签名的 `r` 重建相同 `更新 HH:MM`。这反映服务器可确认的成功响应时间，而不是无法由服务器证明的 Nook 实际刷屏时刻。
- 生产 preview 的 5 图均为 mode `1`、600×800、无截断/越界。metadata：普通整卦 (todo 42/header 40/body 22/reminder 50/divider 355/height 654)，普通单爻 (48/40/40/50/450/697)，长待办 (32/40/22/50/402/701)，长易经坤卦 (38/40/22/50/320/700)，双压力 (24/40/22/50/322/702)。实际长坤卦在正文已经到 22 px 后仍有压力，才进一步缩小待办；这解释了其 divider 与普通乾卦并非相同。
- 本轮 typography 修正：左栏不再有独立 todo/header/body fit。候选 `S=40,38,...,22` 同时测量标题、待办、divider gaps、易经 heading 和全部易经正文；最大完整候选成为 `left_font_size`。五张新图的共享字号为 28、40、24、24、22；右提醒均为 50；均无 overflow/truncation。标题与易经 heading/卦名/爻名只使用 stroke bold，正文保持 regular。
- 共享字号修正后的最终 metadata：01 `28/50/215`，02 `40/50/340`，03 `24/50/301`，04 `24/50/185`，05 `22/50/283`（格式为 shared-left/reminder/divider）。极端无法完整容纳的内容现在抛出安全 renderer error，不再省略或跨越 footer；五个指定 preview 均可完整显示。

## Fixed v2 Production Renderer Wiring（2026-10-02，进行中）

- 现有正式 `screen_state` 访问只选择/更新 `text, updated_at`；仓库内没有 `daily_reminder_text`、`yijing_position`、易经 catalog 或 Stage 2C migration。现有 `TodoProvider` 同样只读 `text,updated_at`，而 `TodoRenderer` 是单段居中渲染，尚未使用 600×800 分区版式。
- 本轮最小状态方案：保留 `text` 作为短期待办，新增 `daily_reminder_text` 与 `yijing_position`；仅新增待执行的本地 SQL migration，并扩展 authenticated 的列级 UPDATE grant，不改变 RLS/policy、不连接或修改线上 Supabase。
- 因用户未提供正式《周易》资料，不能擅自收集/制造完整语料。本轮只接入此前用户提供的乾卦整卦与初九两页作为最小 catalog，用于验证手动上一条/下一条 position；不自动轮换、不随机、不按时间推进。
- 正式 layout 选择 fixed v2：x=392、左横线 y=373、footer 顶线 y=746；待办、易经、右栏各自 fit。flow preview 保留，但不进入默认 renderer；若 fixed-v2 最小字号仍 overflow，本轮优先采用 fixed-v2 only + 显式 overflow detection，而不是静默 fallback。
- 已由 production `TodoRenderer.render_portrait()` 首次生成五张 review PNG：常规整卦 42/34 px、单爻 42/40 px、长待办 26/34 px、长易经 42/24 px、双压力 26/24 px（todo/Yijing），均为 600×800 mode `1`、无 overflow、无 flow fallback。双压力 fixed-v2 因此不需要 fallback。
- 初次图面检查发现 production 易经首行直接绘制 `☰` 会显示 bundled Noto 的缺字方框；这与 preview 已知字体覆盖限制一致。已将 renderer 改为复用 preview 的 1-bit 乾卦/三爻线条兼容画法，待重新生成五图后复核。该修正不更换字体或生产方向。
- 重新生成并目视复核常规整卦与长易经图，首行已不再出现缺字方框；固定分线、右栏、footer 均保持预览确定的坐标，所有五图的 metadata 都是 `mode=1`、600×800、overflow=false、fallback=false。
- `fixed_v2_layout.py` 是 preview 和 production 共用的 geometry/自动换行/fit source。production 输出仍在最后逆时针旋转为已实机验证的 800×600 PNG；本地 `production_previews/` 保留的是旋转前 600×800 人工审查图。
- 全量自动测试为 66/66；包括 fixed v2 常规整卦/单爻、长待办、长易经、双压力、固定 y=373、独立字号、overflow detection、位置不因 render 改变、editor/store/migration 接线和既有 BYOS/signing/cache 回归。所有前端 JS 也通过 `node --check`。

## 连续流式左区 Preview（2026-10-02，进行中）

- 新 preview 只画 x=392 竖线和 y=746 状态栏线；左侧不再画 y=258 或 y=373 横线。待办完成后以 10 px 上下间距和 1 px 动态横线衔接易经首行。
- 初次生成 metadata：常规整卦共享正文 36 px、单爻 40 px、长待办 32 px、长易经 32 px、双压力 26 px；右栏维持独立 50 px，五个样本均未发生裁断。
- 已目视复核常规整卦与双压力图：标题与底栏没有被覆盖，动态线只在左区 x=26..366；`【标签】` 与正文保持同一 Regular 字重/字号，续行回到 x=26。预览中的卦象仍是已有的 1-bit 线条替代画法，并非生产字体变动。
- 单爻样本能维持 40 px 共享正文，因内容很短而自然留下大片空白；这正说明 flow 不强行把易经拉满 1/2 区。8 条待办样本保持 32 px，易经随其同缩为 32 px，整块仍完整并比固定 1/2 的待办 26 px 更大。
- 同 v2 精确对比：常规整卦 flow=36 px（v2 todo=42、Yijing=34）；单爻 flow=40（v2=42/40）；待办压力 flow=32（v2=26/34）；易经压力 flow=32（v2=42/24）。flow 显著释放了长易经的空间（+8 px）和长待办的空间（+6 px），但共享字号使一方变长时另一方也变小。
- 动态线的 y 值会随左侧字号和待办换行变化：常规整卦 y=270、单爻 y=340、待办压力 y=402、长易经 y=246、双压力 y=346。尤其同一待办在整卦/单爻因易经体量不同而改变字号和分隔线位置，视觉稳定性低于 v2 的固定 y=373；正式版若重视稳定阅读，应优先固定 1/2，若重视压力内容的完整性才考虑 flow。

## 600×800 Layout Preview Baseline (2026-10-02)

- 当前可运行实现位于隔离 worktree `codex/battery-display`；父目录的旧 `master` 是早期代码树，不能作为本轮预览脚本落点。
- 正式 `TodoRenderer` 使用仓库内 `server/assets/fonts/NotoSansCJKsc-Regular.otf`，字体家族为 Noto Sans CJK SC Regular；项目仅随附 Regular 字重和 `LICENSE`（SIL Open Font License 1.1）。预览只能用轻微 `stroke_width=1` 模拟标签/标题加粗，不能声称使用了真 Bold。
- 已实机验证的生产方向不变：先画 upright 600×800 portrait，再用 `Image.Transpose.ROTATE_90` 逆时针预旋转输出 800×600；TRMNL v0.16.0 在 Nook 上顺时针旋转后回到正确竖屏。本轮人工比较文件故意保留未旋转的 600×800 portrait。
- 现有 renderer/test 已验证其输出为 mode `1`、PNG、800×600；本轮的独立脚本不得被 `/api/display`、cache 或 signed URL 导入。
- 首轮可视化输出确认：当前 bundled Noto CJK SC Regular 对 `䷀` 与 `☰` 显示为缺字方框；本机 Segoe UI Symbol 也不能可靠画出六爻 `䷀`。为保证预览真实可读又不引入机器相关字体依赖，preview 对这两个全阳符号改用简单 1-bit 线条绘制。中文和所有正文仍使用 bundled Noto；该 workaround 仅服务版面比较，绝不构成生产 glyph-rendering 方案。正式实现前仍需用户确认可合法随 Render 部署、且覆盖简繁中文和易经符号的字体资产，或接受不用符号的文案方案。
- 完成的 geometry 固定为：竖线 x=392，左上/左下短横线 y=258，底栏顶线 y=746；左/右屏边距 26、右栏内边距 24。左栏正文宽 340；易经 label x=26、label width=58、gap=14、body x=98、body width=268；右栏文本宽 158。
- 整卦页中 `彖曰` 的长正文发生像素自动换行，所有续行从 body x=98 开始；压力页中带 `\n` 的 `大象` 以及无空格长 `彖曰` 均保留这一 hanging indent，没有进入 label 列、分隔线或状态栏。
- 压力页的 8 项待办在固定左上区域触发截断，最后可见行以 `…` 表示；右栏的较长提醒与易经压力正文在本组 B 尺寸下仍可放入。最先受到空间约束的是 258 px 高的左上待办区，其次是 158 px 宽的右栏，不是 268 px 宽的易经正文列。
- 预览采用固定字号，不做自动缩小：某区域行数超过边界时只在最后可见行省略，不跨越边界。所有 9 个生成文件均经脚本复开确认 format=PNG、mode=`1`、size=600×800。

## E1/E2/E3 and Auto-scale Preview Findings (2026-10-02)

- 固定 geometry 不变。`x=26` 到 `body_x=98` 只有 72 px 的 label slot；模拟粗体后两字横排标签在 32 px 可留小间隙、36 px 已贴到正文起点、40 px 需要约 82 px，无法同时保持横排和不侵入正文。E2/E3 因此采用两字竖排标签这一 preview-only 安全替代；自动缩放从 40 每次减 2 px 后选择 34 px 的安全横排字号。
- 初步图面复核：E1 38 px 待办已经因长项目自动换行为约四可见行并截断；E2 44 px 约两项后截断；E3 50 px 在左上只适合约两项、并触发省略。右栏的常规六项提醒在 50 px 仍纵向放得下，但每项三字几乎用满 158 px 宽度。
- 自动缩放常规整卦页维持右栏大字，同时将左上待办和易经文字缩至可完整容纳的值；压力待办按规则缩小且仍需末行省略。长彖曰压力页的正文缩小后保持 `body_x=98` 的悬挂缩进，未跨分隔线或状态栏。
- 生成 metadata 的实际自动值：常规整卦/单爻均为 title=40、todo=32、reminder=50、header=40、label=34、body=40、footer=19；待办压力为 todo=24（仍截断）；长易经压力为 body=24（完整）。自动 label 不是 40 的原因是固定 72 px slot + `stroke_width=1` 的确定性几何限制，而不是纵向空间。
- 固定版结果：E1/E2/E3 的常规右栏均完整；三者左上待办均截断，E3 整卦页易经内容也截断。E2/E3 的 36/40 px 标签以竖排两字保持分列；这证明“固定大字号 + 固定 geometry + 横排两字标签”三者不能同时成立。
- 推荐仅基于本地 PNG：固定字号优先 E1（整卦内容完整、仍明显比旧 B 大）；E2 更适合单爻页或接受竖排标签的场景；E3 是清楚的远距离上限测试，不适合作为包含整卦的通用固定版。自动缩放最适合作为正式方向，因为常规时保留 50 px 提醒和 40 px 易经正文，压力内容才局部缩小/省略。Nook 的实际反差、1 px 分隔线可见性仍需实机确认。

## Equal-height / No-label-column Preview v2 (2026-10-02)

- v2 使用左侧分线 `y=373`，左上高度 373、左下高度 373（状态栏前），右栏仍从 y=0 贯穿到 y=746。易经正文从 x=26 开始，宽度 340；没有 label width、body_x、hanging indent 或独立标签样式。
- 初轮 v2 图面确认取消 label 列使段落横向空间完整，但简单逐字 wrap 会把中文 `。` / `，` 单独置于行首或成单字符行。第一版禁则虽移除了孤立标点，却产生 `勿。` / `用` 这种不自然拆分；改为将末尾两个汉字与 closing punctuation 一起移入下一行后重新生成。此问题及修复仅存在于独立 preview helper，不修改正式 renderer。
- v2 最终 metadata：常规整卦为 todo=42、reminder=50、header=40、body=34、footer=19；常规单爻为 42/50/40/40/19；8 条待办压力为 todo=26，完整；长易经压力为 body=24，完整。所有 v2 PNG 的 clipped flags 均为 false。
- 同字号横向行数比较（v2 340 px 全段落，旧逻辑 268 px body-only hanging indent）：常规整卦为 6 vs 7，减少 1 行；长易经压力为 9 vs 10，减少 1 行。单爻内容在 40 px 时为 4 vs 3，因 `【爻辭】`/`【小象】` 本身占用字符，并不存在需要回收的长段落空间；不能把它误报为布局退化。
- 等高调整把易经区从原先 488 px 缩至 373 px（少 115 px）。取消 label 列把可用行宽由 268 增至 340（多 72 px，约 27%），可减少长文换行，但不能完全抵消高度损失：常规整卦正文从旧 auto 的 40 px 降至 v2 的 34 px；长文压力两版均落到 24 px。

## Battery-display Design Audit (2026-09-21)

- 审计范围为只读设计与源码核对：不修改 FastAPI、renderer、Supabase、Render、Nook 或 Git 历史。
- 客户端证据锁定到 `usetrmnl/trmnl-nook-simple-touch` 的实际 tag `v0.16.0`，Git tag object 为 `a1a102dc779c8e57d78ea9ae2b33d9b21bb315af`。后续结论必须以该 tag 的源码为准，而非当前 main 或通用 TRMNL API 文档。
- `DisplayActivity.getBatteryPercent()` 读取 Android `ACTION_BATTERY_CHANGED` 的 `EXTRA_LEVEL` / `EXTRA_SCALE`，按 `Math.round(level * 100f / scale)` 产出整数 0–100；不可用时返回 -1。实际 API header 为大小写写作 `Percent-Charged: <整数>`（例如 57 发送 `57`），不会附 `%`，不是 0–1 小数或电压值。
- 同一 fetch 路径还会在可用时发送 `rssi: <整数 dBm>`；v0.16.0 的 API header 集合为 `User-Agent`、`Accept`、可配置的 `ID` / `access-token`、以及可用时的 `Percent-Charged` / `rssi`。源码未读取或发送 `EXTRA_VOLTAGE`、`EXTRA_STATUS`、`EXTRA_PLUGGED` 等充电/电压状态。
- `startFetch()` 在常规、闹钟唤醒及深度休眠后的刷新路径中启动 `ApiFetchTask`；task 每次启动都会重新读取电量和 RSSI，再构造请求 header。若 battery receiver/level/scale 不可用，电量 header 缺失而请求仍继续。
- 当前 FastAPI 只从 `/api/display` 读取 `ID` 和 `access-token`；`Percent-Charged`、`rssi` 和其他设备状态均未读取、解析、记录或传给 `DisplayService`。现有 tests 也没有这些 header 的覆盖。
- 当前 `NormalizedContent` 只含 `type/body/updated_at`，`content_version()` 仅哈希 `updated_at`；`DisplayService.current()` 以此 version 命中两版本 `ArtifactCache`。因此 Todo 不变时，即使 Nook 电量变化，也会复用旧 PNG 与旧 signed image URL。
- 现有 signer 只允许 20 位小写十六进制 `v`；`for_version(v)` 在 cache miss 时只能从 Supabase 内容重新推导 version。若显示 version 改为不可逆 hash(`content_version + battery`)，必须同时把已签名的电量状态（或可逆 bucket）带入并签名，否则 cache miss 无法安全重建同一 PNG。
- 推荐未来实现使用**精确整数百分比**而不是 5%/10% bucket：仅在 `Percent-Charged` 真的改变时重渲染，300 秒唤醒本身仍会发生，额外 PNG 排版成本很小；这可保证 `电量 63%` 不会被缓存成 60% 或 65%。缺失/非法值使用 `None` 状态并完全不绘制 footer。
- 为保持 content provider 独立，`NormalizedContent` 不应加入电量。建议路由解析可选 header 后把 `battery_percent: int | None` 作为显示请求状态传给 `DisplayService` 和 renderer；保持 Supabase 表、RLS 与 editor 不变。
- 推荐 `display_version = sha256(content_version + "\\0" + battery_state).hexdigest()[:20]`。签名 URL 增加经过 HMAC 覆盖的 `b=<0..100|none>`；`for_version(v, b)` 重载 Supabase 后以同一 `b` 重算 version、渲染并比较。这样既不暴露正文，又解决 cache miss 的可重建性；签名 URL 的有效期、410 stale 逻辑和两版本 cache 模型保持。
- 右下角 footer 推荐一直预留约 56 px：正文区保持左/上 44 px 边距、底部收至约 y=700；footer 以现有 Noto Sans CJK SC Regular 18 px、右/下 44 px 边距绘制。文案：`>=20` 为 `电量 XX%`，`10–19` 为 `电量 XX% · 请充电`，`<10` 为 `电量 XX% · 充电！`；黑字白底、无图标。300 字正文仍在缩小字号/截断保护内。
- 解析策略：只接受去除空白后的十进制整数 `0..100`；缺失、空、`57%`、浮点、非数字和越界均回退为无电量 footer，API 继续生成正文 PNG。仅记录不含 header 原值或凭据的低敏感 warning（或计数），不得导致 500/503。

## Battery Display Local Implementation (2026-09-21)

- 独立开发分支为 `codex/battery-display`，基线为 `origin/main@f3a6551`；上一轮仅改动 planning 文档，已保留在本轮本地差异中。
- 实现保持 `NormalizedContent` 与 TodoProvider 只描述/读取 Supabase 用户内容。`Percent-Charged` 仅由 API 解析后传入 DisplayService 和 renderer；不读取 RSSI，不写任何设备状态回 Supabase。
- `content_version()` 保留原有 `updated_at` 语义。新 `display_version(content, battery_percent)` 哈希 `content_version + NUL + battery_state`，其中 state 为规范 `0..100` 或 `none`。相同 Todo/电量复用 artifact；任一状态变化均新建 artifact。
- Signed image URL 增加 `b`，canonical HMAC message 依次覆盖 `GET`、path、`v`、`b`、`exp`。cache miss 时从经验证的 URL state 重新计算 display version，拒绝版本不匹配的 stale 内容。
- Renderer 永久预留 56 px footer 区域以避免设备偶发缺失 header 时正文跳动；使用现有 Noto Sans CJK SC 18 px、44 px 右/下安全边距和右对齐文案。
- `ScreenArtifact` 也保存规范 battery state。虽然合法签名已把 `v` 与 `b` 绑定，DisplayService 在 cache hit 时仍二次确认 artifact state，避免直接 service 调用或未来接线错误返回 footer 不匹配的 PNG。
- 最终本地验证为 Python compile、58/58 unittest、`git diff --check` 通过；测试覆盖合法/非法 header、三档 footer、300 字与大量换行布局、Todo/电量 version 变化、签名 `b` 篡改、cache hit/miss 与 stale 路径。Stage 1 runtime 13/13 和 Stage 2B-1 校准 generator/PNG 相对 origin/main 无差异。

## Stage 2B-2 Real-device Verification (2026-09-03)

- **Stage 2B-2：COMPLETED / VERIFIED。** GitHub main 已包含实现（implementation `c4bcddc`，PR merge `fb5cb27`），真实端到端链路已在 Nook Simple Touch BNRV300 上通过。
- 已验证链路为：手机 editor → 真实 Supabase `screen_state.main` → Render/FastAPI → TodoProvider → NormalizedContent → 中文 renderer → 800×600 预旋转黑白 PNG → 短期 signed image URL → TRMNL Nook Client v0.16.0 → Nook 实际显示。
- 动态内容来自真实 Supabase，不是 mock、test fixture 或固定 TEST 01 图；Nook 显示的是手机输入的同一份真实内容。
- 公网 `/health`、设备认证 `/api/display`、包含 `v`/`exp`/`sig` 的动态 URL 以及无额外 header 的图片下载均已实际通过；记录中不保存完整签名 URL。
- 中文字体、中文/英文与用户手动换行正常。Stage 2B-1 已验证的 800×600 预旋转规则继续成立，不因拍照或设备摆放方向调整 renderer。
- 当前已验证网络为手机热点，刷新测试值为 300 秒。校园网 PEAP、Render Free 长期 spin-down/cold-start、正式刷新周期仍是独立后续事项；Auto-Deploy 当前人为设为 Off。
- poetry、quote、countdown、calendar、外壳/磁吸安装和长期供电尚未开始，不构成本阶段 VERIFIED 的阻塞项。

## Stage 2B-2 Implementation Findings (2026-09-01)

- 正式实现基线：`origin/main@a4b4a74`，隔离分支 `codex/stage-2b2-local`；Stage 1 runtime 和 Stage 2B-1 校准接口必须保持回归一致。
- Supabase 新版 `sb_secret_...` key 不是 JWT。官方当前说明应把它放在 `apikey` request header；本实现不发送 `Authorization: Bearer <secret>`，不把 secret 放 URL、日志、异常、Nook 或前端。
- provider 唯一 REST 请求固定为 `GET {SUPABASE_URL}/rest/v1/screen_state?id=eq.main&select=text,updated_at`；所有测试使用 `httpx.MockTransport`/测试值，不连接真实 Supabase。
- 字体来源锁定官方 `notofonts/noto-cjk`：`Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf`，仅保留 Regular。对应 `Sans/LICENSE` 明确为 SIL Open Font License 1.1，允许随软件分发但必须附许可证。
- Renderer 必须显式加载项目内 `server/assets/fonts/NotoSansCJKsc-Regular.otf`，不做系统字体 discovery；先绘制 upright 600×800，再 `ROTATE_90` 输出 800×600。
- Sources:
  - https://supabase.com/docs/guides/getting-started/api-keys
  - https://github.com/notofonts/noto-cjk/tree/main/Sans/OTF/SimplifiedChinese
  - https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE
- Bundled font SHA-256: `2C76254F6FC379FDDFCE0A7E84FB5385BB135D3E399294F6EEB6680D0365B74B`; bundled license SHA-256: `6A73F9541C2DE74158C0E7CF6B0A58EF774F5A780BF191F2D7EC9CC53EFE2BF2`.
- Final local verification: Python compile passed; 48/48 unittest passed; diff check and secret scan passed; Stage 1 runtime 13/13 unchanged from `a4b4a74`; Stage 2B-1 calibration generator and PNG unchanged.
- Stage 2B-2 is **LOCAL IMPLEMENTATION ONLY**, not deployed or device-verified. No live Supabase request was made.

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
