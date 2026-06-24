import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

console.log('🚀 开始半自动发版流程...\n');

// 1. build
console.log('📦 正在执行 npm run build...');
execSync('npm run build', { stdio: 'inherit' });

console.log('\n✅ build 完成');

// 2. 检查 dist
const distPath = path.join(process.cwd(), 'dist');

if (!fs.existsSync(distPath)) {
  console.log('❌ dist 不存在，请检查 build');
  process.exit(1);
}

console.log('📁 dist 已生成');

// 3. 提示上传
console.log('\n☁️ 请手动上传 dist 到 CloudBase 静态托管');
console.log('路径：', distPath);

// 4. 云函数提示
console.log('\n🔧 如果修改了云函数，请手动上传 cloudfunctions/medicineApi');

// 5. 版本号
const version = `v1.${Date.now()}`;
console.log('\n🎉 发版完成！');
console.log('📌 当前版本号：', version);
