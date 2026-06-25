import { DATA_MODE } from '../constants';
import { ensureCloudAuth, getCloudApp, logCloudBaseError } from './cloudbaseClient';

const tempUrlCache = new Map<string, string>();

console.info('[medicineStorage] data mode:', DATA_MODE);

function fileToDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(reader.error || new Error('图片读取失败'));
    reader.readAsDataURL(file);
  });
}

function buildImagePath(file: File) {
  const extension = file.name.split('.').pop()?.toLowerCase().replace(/[^a-z0-9]/g, '') || 'jpg';
  return `medicines/${Date.now()}-${Math.random().toString(16).slice(2)}.${extension}`;
}

export function isCloudFileId(value: string) {
  return value.startsWith('cloud://');
}

function isHttpUrl(value: string) {
  return value.startsWith('http://') || value.startsWith('https://');
}

function isDataImageUrl(value: string) {
  return value.startsWith('data:image');
}

function getImageUrlPrefix(value: string) {
  return value.slice(0, 80);
}

export function isLikelyHeicImage(file: File) {
  const type = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  return type.includes('heic') || type.includes('heif') || /\.(heic|heif)$/.test(name);
}

export async function uploadMedicineImage(file: File) {
  if (!file) {
    throw new Error('未选择图片');
  }

  if (DATA_MODE === 'mock') {
    console.log('[medicineStorage.uploadMedicineImage] mock upload, returning data URL preview only');
    return fileToDataUrl(file);
  }

  const cloudPath = buildImagePath(file);

  try {
    const app = getCloudApp();
    await ensureCloudAuth();
    console.log('[medicineStorage.uploadMedicineImage] cloudbase upload start:', {
      cloudPath,
      fileType: file.type,
      fileSize: file.size,
    });
    const result = await app.uploadFile({
      cloudPath,
      filePath: file as unknown as string,
    });
    const fileID = String(result.fileID || '').trim();
    console.log('[medicineStorage.uploadMedicineImage] cloudbase upload result:', {
      hasFileID: Boolean(fileID),
      prefix: fileID.slice(0, 16),
    });
    if (!fileID || !isCloudFileId(fileID)) {
      throw new Error('图片上传成功但未返回 CloudBase fileID');
    }
    return fileID;
  } catch (error) {
    logCloudBaseError('Upload medicine image failed', error);
    throw error;
  }
}

export async function resolveTempImageUrl(imageUrl?: string) {
  const value = String(imageUrl || '').trim();
  if (!value) return '';
  if (isHttpUrl(value) || isDataImageUrl(value)) return value;
  if (!isCloudFileId(value)) {
    console.warn('[medicineStorage.resolveMedicineImageUrl] unsupported imageUrl prefix:', getImageUrlPrefix(value));
    return '';
  }
  const cached = tempUrlCache.get(value);
  if (cached) return cached;

  try {
    console.log('[medicineStorage.resolveMedicineImageUrl] resolving cloud fileID:', value.slice(0, 32));
    const app = getCloudApp();
    await ensureCloudAuth();
    const result = await app.getTempFileURL({
      fileList: [value],
    });
    const tempUrl = result.fileList?.[0]?.tempFileURL || '';
    console.log('[medicineStorage.resolveMedicineImageUrl] resolved tempUrl prefix:', getImageUrlPrefix(tempUrl));
    if (tempUrl) {
      tempUrlCache.set(value, tempUrl);
      return tempUrl;
    }
    return '';
  } catch (error) {
    logCloudBaseError('Resolve medicine image URL failed', error);
    return '';
  }
}

export const resolveMedicineImageUrl = resolveTempImageUrl;
