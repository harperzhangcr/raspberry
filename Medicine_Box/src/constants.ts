export const DEFAULT_CATEGORIES = [
  '发烧止痛',
  '感冒',
  '咳嗽',
  '胃肠道',
  '高血压',
  '高尿酸',
  '高血脂',
  '皮肤',
  '过敏',
  '眼科',
  '其他',
];

export const FAMILY_CODE_STORAGE_KEY = 'family_medicine_box_code';

const rawDataMode = String(import.meta.env.VITE_DATA_MODE || '').trim().toLowerCase();
const hasCloudBaseEnvId = Boolean(String(import.meta.env.VITE_CLOUDBASE_ENV_ID || '').trim());

export const DATA_MODE = rawDataMode === 'cloudbase' || rawDataMode === 'mock'
  ? rawDataMode
  : hasCloudBaseEnvId
    ? 'cloudbase'
    : 'mock';
