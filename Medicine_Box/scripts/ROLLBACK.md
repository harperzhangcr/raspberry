# Rollback Guide

## 查看历史版本

每次执行：

```bash
npm run deploy
```

都会在项目根目录生成一个版本快照目录：

```text
dist-versions/vX.X.X/
```

例如：

```text
dist-versions/v1.0.3/
```

可以通过查看 `dist-versions` 下的目录确认历史版本。

## 回滚步骤

1. 在 `dist-versions/` 中选择要恢复的版本，例如：

```text
dist-versions/v1.0.2/
```

2. 将该目录内容上传到 CloudBase 静态网站托管。

3. 上传完成后，线上页面会恢复到该静态前端版本。

## 注意事项

- rollback 只替换 CloudBase 静态网站托管中的前端文件。
- rollback 不会修改 CloudBase 数据库。
- rollback 不会修改云函数。
- 如果历史版本依赖某个特定云函数版本，需要人工确认云函数是否兼容。

