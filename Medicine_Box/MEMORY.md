# Project Memory

## Project Facts
- Project name: raspberry
- Created date: 2026-06-21
- Product: 家庭药箱管理 H5 应用
- Core goal: 家庭成员在需要某类药时，快速知道家里有没有、有哪些、库存多少、是否过期、是否缺货。
- Tech stack: Vue 3, Vite, TypeScript, Vant 4, CloudBase Web SDK, CloudBase 云函数, CloudBase 云数据库, CloudBase 静态网站托管。

## Long-Term Decisions
- 首页采用「分类药箱目录」结构，而不是以过期/缺货报表为首页中心。
- 前端统一调用 `medicineApi` 云函数，禁止直接操作 CloudBase 云数据库。
- 家庭访问码由 `medicineApi` 读取环境变量 `FAMILY_CODE` 校验，前端只保存用户输入的访问码到 `localStorage`。
- 本地开发默认支持 mock 数据模式，避免 CloudBase 环境未配置时阻塞界面开发和家庭试用。
- CloudBase 初始化集中在 `src/services/medicineApi.ts`，并使用匿名登录态调用云函数，不做业务登录注册。
- 分类不单独建集合；药品分类直接存入 `medicines.category`，修改分类时批量更新对应药品。未绑定药品的自定义分类存入浏览器 `localStorage`。
- CloudBase 云函数入口为 `cloudfunctions/medicineApi/index.js`，支持 `list/add/update/delete/adjustQuantity/addBatch` action。
- UI 主题变量集中在 `src/styles/theme.css`，全局入口保留 `src/styles.css`；视觉规范通过 CSS Variables 管理，组件内只保留布局样式。
- H5 主内容最大宽度控制为 480px，优先适配手机端，并通过 safe-area 变量保护底部操作区域。
- 首页分类模块默认折叠，点击分类头后展开；搜索药品时自动展开匹配分类，避免搜索结果被隐藏。
- 默认分类清单为 11 类：发烧止痛、感冒、咳嗽、胃肠道、高血压、高尿酸、高血脂、皮肤、过敏、眼科、其他。
- 首页分类横幅采用 AI 生成底图 + 本地叠加中文标题，再统一压缩为 webp，避免生成模型中文乱码并控制首页加载体积。
- 首页分类横幅左侧标题区应保持原有样式：不规则撕碎纸片色块作为底，叠加白色半透明圆角模块，中文标题和“药箱”胶囊放在模块内。
- 高尿酸分类横幅避免使用脚/脚趾作为患处图案；用户反馈脚部图案容易引发不适，后续应改用手指、肘部、膝关节等更克制的患处表达。
- Medicine 数据结构长期只保留 `updatedAt`，不再使用 `createdAt`；云函数新增药品不写 `createdAt`，编辑或库存调整时会清理旧文档中的 `createdAt`。
- Medicine 库存采用批次模型：`batches` 保存每批 `expiryDate + quantity`，`quantity` 是批次数量合计，`expiryDate` 是最近一批有效期，用于列表、状态和旧数据兼容。
- 库存增加可走 `addBatch` 录入明确有效期和数量；`adjustQuantity` 支持 `-1` 和 `1`，并优先调整最近过期批次。若 `+1` 时没有批次，则用当前 `expiryDate` 创建一批。
- 状态筛选语义中，`有正常效期库存` 代表库存数量大于 0 且未过期；30 天内过期仍属于正常效期库存，已过期即使仍有数量也不属于该筛选。该状态只作为筛选项，不作为药品卡片标签展示。
- 批次编辑采用卡片内 inline 编辑：点击批次行后直接编辑 `expiryDate` 和 `quantity`，失焦或回车自动保存；不新增弹窗和单独编辑按钮。
- 药品图片 AI 识别统一走 CloudBase 云函数 `medicineApi` 的 `aiRecognizeMedicine` action；前端只传 CloudBase fileID/URL，不持有或调用 AI API Key。阿里百炼 API Key 必须配置在云函数环境变量 `ALI_API_KEY`。
- `npm run deploy` 是半自动发版入口：自动递增 package patch 版本、执行前端 build、生成 `dist/version.txt` 和 `dist/version.json`、保存 `dist-versions/vX.X.X/` 快照，并提示用户手动上传 `dist` 到 CloudBase 静态托管；云函数仍按需手动上传。
- rollback 通过手动上传 `dist-versions/vX.X.X/` 的历史静态文件到 CloudBase 静态托管完成，不影响 CloudBase 数据库。

## Resource Paths
- Project root: `/Users/zhangcongrong/Documents/raspberry/Medicine_Box`
- Frontend entry: `/Users/zhangcongrong/Documents/raspberry/Medicine_Box/src/App.vue`
- API service: `/Users/zhangcongrong/Documents/raspberry/Medicine_Box/src/services/medicineApi.ts`
- Category assets: `/Users/zhangcongrong/Documents/raspberry/Medicine_Box/src/assets/categories`
- Category asset mapping: `/Users/zhangcongrong/Documents/raspberry/Medicine_Box/src/categoryAssets.ts`
- Cloud function: `/Users/zhangcongrong/Documents/raspberry/Medicine_Box/cloudfunctions/medicineApi/index.js`
- Qwen-VL wrapper: `/Users/chocho/Documents/raspberry/Medicine_Box/cloudfunctions/medicineApi/qwen.js`
- Deploy script: `/Users/chocho/Documents/raspberry/Medicine_Box/scripts/deploy.js`
- Rollback guide: `/Users/chocho/Documents/raspberry/Medicine_Box/scripts/ROLLBACK.md`
- Deployment guide: `/Users/zhangcongrong/Documents/raspberry/Medicine_Box/README.md`
- Codex proxy env file: `/Users/zhangcongrong/.codex/.env`
- CloudBase envId: `family-medicine-box-d4bsdb25e54e`

## Verification Records
- 2026-06-21: `npm run build` passed. Vite reported a large chunk warning caused mainly by bundled dependencies; it does not block family self-use deployment.
- 2026-06-21: `node -c cloudfunctions/medicineApi/index.js` passed.
- 2026-06-21: Local dev server started at `http://localhost:5173/` after port-listening approval.
- 2026-06-21: UI/mobile upgrade build passed. Browser checks at 320px, 390px, 430px, and 768px found no horizontal overflow; form popup at 390px had 56px field height and 52px save button height.
- 2026-06-21: Fixed tabs alignment by scoping higher-specificity styles to `.tabs-shell`; Vant default `.van-tabs--line .van-tabs__wrap` height had overridden the custom segmented control height.
- 2026-06-21: Fixed bottom sheet alignment on wide viewports by centering `.van-popup--bottom.sheet-popup`; Vant bottom popup defaults to `left: 0`, which made max-width sheets appear in the lower-left corner.
- 2026-06-21: Category collapse and detail field update passed build and browser checks; default category cards are collapsed, first category expands to show 3 cards, detail panel shows `更新时间` and no `创建时间`, and note row uses left label/right value layout.
- 2026-06-21: Detail note row visual alignment fixed; note value color now matches Vant cell value color and the row uses matching inset divider lines above and below.
- 2026-06-21: Removed duplicate top divider on detail note row and centered form/category-manager row contents; browser check confirmed no note `::before` divider and label/body center deltas are 0.
- 2026-06-21: Category manager add/edit action buttons aligned by giving the add row the same horizontal inset and 72px action column as category edit rows; browser check confirmed left/right deltas are 0.
- 2026-06-21: Batch inventory feature added. `+` opens an add-stock sheet with expiry date and quantity, cards can expand batch details sorted by earliest expiry, and `-1` deducts from the earliest-expiring batch first. Build and cloud function syntax checks passed; browser check confirmed batch rows and add-stock fields.
- 2026-06-21: Tightened inventory adjustment contract so `adjustQuantity` only accepts `-1`; build and cloud function syntax checks passed.
- 2026-06-21: Added 9 category webp banners under `src/assets/categories` and wired them into homepage category headers. `npm run build` passed; browser check at 390px confirmed images loaded, no horizontal overflow, and category labels remained readable.
- 2026-06-21: Fixed all-list filter dropdown option visibility by scoping Vant dropdown item content/cell text styles; global `.van-cell__title` muted color and transparent cell background should not leak into dropdown options. `npm run build` passed; browser check confirmed category/status dropdown options render on solid white background with readable text.
- 2026-06-22: Fixed all-list filter dropdown positioning by removing `animated swipeable` from `van-tabs`; Vant dropdown popups should not live inside transformed swipe tracks because fixed/absolute coordinates are shifted, pushing option text offscreen. `npm run build` passed; browser check confirmed category/status dropdowns open directly below the filter bar with visible text.
- 2026-06-22: Updated `medicineApi.adjustQuantity` to accept `delta = -1` and `delta = 1`; `-1` cannot reduce stock below zero, `+1` adjusts the earliest-expiring batch or creates one from current `expiryDate` when no batch exists. `node -c cloudfunctions/medicineApi/index.js` and `npm run build` passed.
- 2026-06-22: Constrained Vant dropdown content width to the same responsive content column as medicine cards using `min(100vw - 32px, 448px)` logic via CSS variables. Avoid using CSS `translate` on `.van-dropdown-item__content` because it conflicts with Vant popup positioning/animation; use calculated `left` instead. `npm run build` passed; browser checks at 599px and 390px confirmed dropdown width equals filter bar width and opens below it.
- 2026-06-22: Configured local `.env` for CloudBase mode with `VITE_DATA_MODE=cloudbase` and `VITE_CLOUDBASE_ENV_ID=family-medicine-box-d4bsdb25e54e`. `npm run build` passed.
- 2026-06-22: Replaced CloudBase Web SDK anonymous auth from deprecated `anonymousAuthProvider().signIn()` to `auth.signInAnonymously()` in `src/services/medicineApi.ts`, with login-state reuse, retry after auth failure, and clearer CloudBase error logs. `npm run build` passed; browser check showed the previous `scope` error was gone, but CloudBase console still needs 匿名登录 enabled.
- 2026-06-22: Moved the project working directory under `/Users/zhangcongrong/Documents/raspberry/Medicine_Box`; future work should use this directory as cwd. The parent `/Users/zhangcongrong/Documents/raspberry` retains `.git` repository metadata.
- 2026-06-22: Added optional Medicine fields `location` and `imageUrl`. Medicine data writes still go through `medicineApi` cloud function, while photos upload through CloudBase Storage via `src/services/medicineStorage.ts`; `imageUrl` stores the CloudBase fileID and UI resolves temporary URLs only for preview/display. Old medicines without these fields remain compatible. `node -c cloudfunctions/medicineApi/index.js` and `npm run build` passed.
- 2026-06-23: Added recycle bin soft-delete flow. `delete` now writes `deletedAt`/`updatedAt`, `list` hides deleted medicines, `listDeleted` returns deleted items by newest deletion, `restore` removes `deletedAt`, and `permanentDelete` is the only path that removes a document. Frontend adds a lightweight recycle bin sheet with restore/permanent delete actions. `node -c cloudfunctions/medicineApi/index.js` and `npm run build` passed.
- 2026-06-23: Added same-name medicine merge behavior. New medicines are matched by `name.trim().toLowerCase()` against non-deleted medicines; the frontend asks whether to join inventory, and the cloud function `add` also falls back to appending a batch instead of creating a duplicate document. Existing batch/FIFO behavior is unchanged. `node -c cloudfunctions/medicineApi/index.js` and `npm run build` passed.
- 2026-06-23: Fixed same-name merge metadata and form reset. When merging into an existing medicine, `imageUrl`, `location`, and `note` are supplemented only if the existing field is empty; existing values are never overwritten. New/edit form instances are remounted on open so create form state does not retain the previous medicine, while edit still backfills correctly. `node -c cloudfunctions/medicineApi/index.js` and `npm run build` passed.
- 2026-06-24: Completed P0 data consistency convergence. Batch normalization now merges identical `expiryDate` batches and keeps FIFO ordering, `MedicineBatch.createdAt` is required in the frontend type and auto-filled for legacy data, mock/cloud add/addBatch/adjustQuantity paths share the same normalization behavior, update rejects renaming to an existing non-deleted medicine name, and the duplicate-name prompt text was aligned to “已存在同名药品，是否加入库存？”. `node -c cloudfunctions/medicineApi/index.js` and `npm run build` passed.
- 2026-06-24: Upgraded create flow to no-dialog same-name recognition. `MedicineForm` can query `medicineApi.findByName` while typing in create mode, auto-prefill image/location/note/category/unit from an existing non-deleted medicine, lock the name field, and submit the matched medicine to `App.vue`. Save now updates allowed master fields and always calls `addBatch`; the previous “加入库存” confirmation dialog was removed. Cloud function added `findByName`. `node -c cloudfunctions/medicineApi/index.js` and `npm run build` passed.
- 2026-06-24: Added `高尿酸` and `高血脂` default categories with matching webp banners under `src/assets/categories`; titles are rendered locally over AI-generated no-text backgrounds to preserve Chinese text accuracy.
- 2026-06-24: Added semi-automatic deploy script at `scripts/deploy.js`. Because the project uses `"type": "module"`, the script uses ESM imports instead of CommonJS `require`. `node --check scripts/deploy.js` and `npm run deploy` passed.
- 2026-06-24: Completed P1 UI/interaction fixes. The all-list Vant dropdown now has `60vh` scrollable content, higher overlay/dropdown z-index, and body scroll lock while open. Medicine batch rows now support click-to-edit inline `expiryDate` and `quantity`, auto-saving on blur/Enter through `updateBatch` while preserving the existing batch normalization model. `node -c cloudfunctions/medicineApi/index.js`, `npm run build`, and browser checks at 390px passed.
- 2026-06-24: Fixed all-list dropdown overlay regression. Scope overlay z-index to `.van-dropdown-item .van-overlay`, force `.van-dropdown-item__content` above it, and avoid adding `position: relative` to the content because it interferes with Vant popup hit testing/positioning. Browser coordinate click confirmed status option selection works; `npm run build` passed.
- 2026-06-24: Adjusted stock status semantics. The stock filter label is now `有正常效期库存`, and it includes medicines with quantity greater than 0 whose expiry status is not expired, including expiring-soon medicines. Expired medicines are excluded even if quantity remains. This state is not shown as a medicine card tag; risk tags such as `缺货`, `已过期`, and `30天内过期` remain visible. `npm run build` passed.
- 2026-06-24: Upgraded deploy system to SemVer patch releases and rollback snapshots. `scripts/deploy.js` now reads and increments `package.json` version, builds, writes `version.txt`/`version.json`, archives `dist` to `dist-versions/vX.X.X/`, and prints CloudBase upload plus rollback guidance. Added `scripts/ROLLBACK.md`; `node --check scripts/deploy.js` and `npm run build` passed.
- 2026-06-24: Added CloudBase-mediated Qwen-VL medicine image recognition. `aiRecognizeMedicine` resolves CloudBase fileIDs to temporary URLs, calls Alibaba Bailian OpenAI-compatible chat completions through `cloudfunctions/medicineApi/qwen.js`, and returns `{ name, category, indications }` or `{ error: true, message: 'AI识别失败' }`. Frontend calls it after image upload and maps `indications` into the existing `note` field without changing the Medicine data model. `node -c cloudfunctions/medicineApi/index.js`, `node -c cloudfunctions/medicineApi/qwen.js`, and `npm run build` passed.

## Pending Confirmations
- CloudBase 控制台登录授权需要开启「匿名登录」，否则 `auth.signInAnonymously()` 会返回「登录方式未开启」。
- 线上家庭访问码待用户在 CloudBase 云函数环境变量 `FAMILY_CODE` 中配置。
