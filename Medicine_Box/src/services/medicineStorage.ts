import { DATA_MODE } from '../constants';
import { ensureCloudAuth, getCloudApp, logCloudBaseError } from './cloudbaseClient';

const tempUrlCache = new Map<string, string>();

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

export async function uploadMedicineImage(file: File) {
  if (DATA_MODE === 'mock') {
    return fileToDataUrl(file);
  }

  const cloudPath = buildImagePath(file);

  try {
    const app = getCloudApp();
    await ensureCloudAuth();
    const result = await app.uploadFile({
      cloudPath,
      filePath: file as unknown as string,
    });
    return result.fileID;
  } catch (error) {
    logCloudBaseError('Upload medicine image failed', error);
    throw error;
  }
}

export async function resolveMedicineImageUrl(imageUrl?: string) {
  const value = String(imageUrl || '').trim();
  if (!value) return '';
  if (!isCloudFileId(value)) return value;
  const cached = tempUrlCache.get(value);
  if (cached) return cached;

  try {
    const app = getCloudApp();
    await ensureCloudAuth();
    const result = await app.getTempFileURL({
      fileList: [value],
    });
    const tempUrl = result.fileList?.[0]?.tempFileURL || '';
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
