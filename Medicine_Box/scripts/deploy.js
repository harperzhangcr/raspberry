import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const rootDir = process.cwd();
const packagePath = path.join(rootDir, 'package.json');
const distPath = path.join(rootDir, 'dist');
const versionRootPath = path.join(rootDir, 'dist-versions');

function readPackageJson() {
  return JSON.parse(fs.readFileSync(packagePath, 'utf8'));
}

function writePackageJson(packageJson) {
  fs.writeFileSync(packagePath, `${JSON.stringify(packageJson, null, 2)}\n`);
}

function parseSemver(version) {
  const match = String(version || '').trim().match(/^v?(\d+)\.(\d+)\.(\d+)$/);
  if (!match) {
    throw new Error(`package.json version 必须是 SemVer 格式，例如 1.0.0。当前值：${version}`);
  }

  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
  };
}

function bumpPatch(version) {
  const current = parseSemver(version);
  return `${current.major}.${current.minor}.${current.patch + 1}`;
}

function ensureDistExists() {
  if (!fs.existsSync(distPath)) {
    throw new Error('dist 不存在，请检查 build 是否成功');
  }
}

function writeVersionFiles(versionTag, time) {
  const versionInfo = {
    version: versionTag,
    time,
  };

  fs.writeFileSync(path.join(distPath, 'version.txt'), `${versionTag}\n`);
  fs.writeFileSync(path.join(distPath, 'version.json'), `${JSON.stringify(versionInfo, null, 2)}\n`);
}

function archiveDist(versionTag) {
  const archivePath = path.join(versionRootPath, versionTag);

  if (fs.existsSync(archivePath)) {
    throw new Error(`版本快照已存在：${archivePath}`);
  }

  fs.mkdirSync(versionRootPath, { recursive: true });
  fs.cpSync(distPath, archivePath, { recursive: true });
  return archivePath;
}

let originalPackageJson = null;
let packageVersionUpdated = false;

console.log('🚀 开始半自动发版流程...\n');

try {
  const packageJson = readPackageJson();
  originalPackageJson = { ...packageJson };
  const nextVersion = bumpPatch(packageJson.version);
  const versionTag = `v${nextVersion}`;
  const releaseTime = new Date().toISOString();

  packageJson.version = nextVersion;
  writePackageJson(packageJson);
  packageVersionUpdated = true;

  console.log(`🔖 版本递增：${versionTag}`);

  console.log('\n📦 正在执行 npm run build...');
  execSync('npm run build', { stdio: 'inherit' });
  console.log('\n✅ build 完成');

  ensureDistExists();
  console.log('📁 dist 已生成');

  writeVersionFiles(versionTag, releaseTime);
  console.log('📝 已生成 dist/version.txt 与 dist/version.json');

  const archivePath = archiveDist(versionTag);
  console.log('🗂️ 已保存版本快照：', archivePath);

  console.log('\n☁️ 请手动上传 dist 到 CloudBase 静态托管');
  console.log('路径：', distPath);

  console.log('\n↩️ rollback 提示');
  console.log(`如需回滚，请选择 dist-versions/${versionTag} 之外的历史版本目录，并手动上传到 CloudBase 静态托管。`);
  console.log('rollback 只替换静态前端文件，不影响 CloudBase 数据库。');
  console.log('详细说明：scripts/ROLLBACK.md');

  console.log('\n🎉 发版准备完成！');
  console.log('📌 当前版本号：', versionTag);
} catch (error) {
  if (packageVersionUpdated && originalPackageJson) {
    writePackageJson(originalPackageJson);
  }

  console.error('\n❌ 发版失败');
  if (packageVersionUpdated && originalPackageJson) {
    console.error(`已恢复 package.json version：${originalPackageJson.version}`);
  }
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
}
