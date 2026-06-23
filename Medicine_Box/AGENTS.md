# Project Instructions

## Project
- Name: raspberry
- Product: 家庭药箱管理 H5 应用
- Target user: 家庭成员自用，无登录注册，通过家庭访问码进入
- Delivery target: 5 小时内完成可自用版本

## Working Language
- Default response language: Chinese
- Code, variables, commands, and skill names: English

## Tech Stack
- Vue 3
- Vite
- TypeScript
- Vant 4
- CloudBase Web SDK
- CloudBase 云函数
- CloudBase 云数据库
- CloudBase 静态网站托管

## Product Principles
- 首页以药品分类为核心组织方式，不做报表式 Dashboard。
- 优先解决家庭成员快速查找药品、判断库存、识别过期和缺货的问题。
- 前端不直接操作 CloudBase 数据库，统一通过云函数访问。
- 家庭访问码只允许在云函数环境变量 `FAMILY_CODE` 中配置，禁止写死在前端代码。

## Engineering Rules
- 代码修改后必须执行可用性校验，至少包括 `npm run build`。
- 本地开发必须支持 mock 数据模式，线上再切换 CloudBase 云函数模式。
- 敏感凭据禁止写入代码仓库，`.env` 仅保留非敏感环境标识或示例。
- Git push 仅用于多设备同步，禁止自动执行。

## Memory Rules
- 每次任务启动先读取 `AGENTS.md` 和 `MEMORY.md`。
- 长期有效的架构决策、踩坑记录、用户修正意见、资源路径需要写入 `MEMORY.md`。
- 会话结束前汇总本次新增记忆条目，等待用户确认。
