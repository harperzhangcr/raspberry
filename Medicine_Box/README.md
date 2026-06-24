# 家庭药箱管理 H5

面向家庭自用的「家庭药箱快速查找 + 库存感知」工具。首页按药品分类组织，优先回答：家里有没有这类药、有哪些药、库存多少、是否过期、是否缺货。

## 文件结构

```text
.
├── AGENTS.md
├── MEMORY.md
├── README.md
├── cloudfunctions
│   └── medicineApi
│       ├── index.js
│       └── package.json
├── index.html
├── package.json
├── src
│   ├── App.vue
│   ├── components
│   │   ├── MedicineCard.vue
│   │   └── MedicineForm.vue
│   ├── constants.ts
│   ├── main.ts
│   ├── services
│   │   ├── medicineApi.ts
│   │   └── mockData.ts
│   ├── styles.css
│   ├── types.ts
│   └── utils
│       └── medicine.ts
├── tsconfig.json
└── vite.config.ts
```

## 核心设计原因

- 首页按分类分组：家庭成员找药时通常先想“发烧止痛药有没有”，不是先看报表，所以分类目录比 Dashboard 更接近真实动作。
- 前端统一调用云函数：访问码和数据库权限集中在服务端，避免前端泄露 `FAMILY_CODE` 或直接暴露数据库写入能力。
- 本地 mock 优先：CloudBase 环境未创建前也能先验证界面和家庭使用流程，5 小时交付风险更低。
- 分类不单独建集合：当前药品规模只有 40-50 种，`category` 字段直接挂在药品上更简单；修改分类时批量更新药品即可。
- 分类横幅采用 AI 生成底图 + 本地叠加中文标题：生成模型负责医学场景插画，本地渲染负责中文准确性，避免图片中文字乱码。

## 上线后对终端用户的实际影响

- 家人打开页面输入一次访问码，后续直接进入药箱。
- 首页直接按「发烧止痛、感冒、咳嗽、胃肠道、高血压、高尿酸、高血脂、皮肤、过敏、眼科、其他」等分类找药，不需要理解筛选报表。
- 分类卡片带有图文横幅，家人扫一眼就能识别药品大类。
- 每张药品卡片直接显示库存、有效期、缺货和过期标签。
- 需要补药时点击 `+` 录入新库存批次和有效期；拿药时点击 `-`，系统优先扣减最近过期的批次。
- 已过期、30 天内过期、缺货会在药品卡片和分类标题中显性提醒。

## 分类横幅资源

分类横幅资源位于：

```text
src/assets/categories
```

图片由 `src/categoryAssets.ts` 统一映射到分类名称，格式为 `webp`，单张约 28-54KB。

## CloudBase 初始化位置

前端 CloudBase 初始化在：

```text
src/services/medicineApi.ts
```

关键代码：

```ts
const app = cloudbase.init({ env });
```

`env` 来自 `VITE_CLOUDBASE_ENV_ID`，不要把家庭访问码写入前端环境变量。

## 本地运行

1. 安装依赖：

```bash
npm install
```

2. 复制环境变量示例：

```bash
cp .env.example .env
```

3. 本地 mock 模式：

```bash
VITE_DATA_MODE=mock
```

4. 启动开发服务：

```bash
npm run dev
```

mock 模式下访问码只要求非空，便于先试用界面。

## 切换到 CloudBase 云函数模式

`.env` 配置：

```bash
VITE_DATA_MODE=cloudbase
VITE_CLOUDBASE_ENV_ID=你的 CloudBase 环境 ID
```

## 创建 CloudBase 环境

1. 打开腾讯云 CloudBase 控制台。
2. 创建一个环境，例如 `family-medicine-prod`。
3. 记录环境 ID，填入前端 `.env` 的 `VITE_CLOUDBASE_ENV_ID`。

## 创建 medicines 集合

在 CloudBase 云数据库中创建集合：

```text
medicines
```

药品结构：

```json
{
  "_id": "数据库自动生成",
  "name": "布洛芬",
  "category": "发烧止痛",
  "quantity": 2,
  "unit": "盒",
  "expiryDate": "2026-12-31",
  "batches": [
    {
      "id": "batch-1760000000000-a1",
      "expiryDate": "2026-12-31",
      "quantity": 2
    }
  ],
  "note": "饭后服",
  "updatedAt": 1760000000000
}
```

`batches` 是真实库存批次；`quantity` 是批次数量合计，`expiryDate` 是最近一批有效期，用于列表排序、状态标签和兼容旧数据。

建议数据库权限设置为仅云函数可写，前端不要直接访问数据库。

## 配置 FAMILY_CODE

在 CloudBase 控制台打开云函数 `medicineApi` 的环境变量配置：

```text
FAMILY_CODE=你的家庭访问码
```

注意：不要把 `FAMILY_CODE` 写入前端代码、`.env` 或 README 的真实值。

## 部署云函数

安装 CloudBase CLI 后登录：

```bash
npm install -g @cloudbase/cli
tcb login
```

进入项目根目录，部署云函数：

```bash
tcb fn deploy medicineApi --dir cloudfunctions/medicineApi --env 你的 CloudBase 环境 ID
```

部署后在控制台给 `medicineApi` 配置环境变量 `FAMILY_CODE`。

## 部署静态网站

1. 构建前端：

```bash
npm run build
```

2. 部署 `dist` 到 CloudBase 静态网站托管：

```bash
tcb hosting deploy dist -e 你的 CloudBase 环境 ID
```

## 本地校验和线上部署命令

本地开发：

```bash
npm run dev
```

生产构建：

```bash
npm run build
```

本地预览构建结果：

```bash
npm run preview
```

部署云函数：

```bash
tcb fn deploy medicineApi --dir cloudfunctions/medicineApi --env 你的 CloudBase 环境 ID
```

部署静态网站：

```bash
tcb hosting deploy dist -e 你的 CloudBase 环境 ID
```

## medicineApi action

云函数路径：

```text
cloudfunctions/medicineApi/index.js
```

支持的 `action`：

- `list`
- `add`
- `update`
- `delete`
- `adjustQuantity`
- `addBatch`

所有 action 都会校验 `familyCode`，与云函数环境变量 `FAMILY_CODE` 比较。
