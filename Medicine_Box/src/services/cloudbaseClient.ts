import cloudbase from '@cloudbase/js-sdk';

let cloudApp: ReturnType<typeof cloudbase.init> | null = null;
let authReady: Promise<void> | null = null;

export function getErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  try {
    return JSON.stringify(error);
  } catch {
    return '未知错误';
  }
}

export function logCloudBaseError(stage: string, error: unknown) {
  console.error(`[CloudBase] ${stage}:`, error);
}

export function getCloudApp() {
  if (cloudApp) return cloudApp;
  const env = import.meta.env.VITE_CLOUDBASE_ENV_ID;
  if (!env) {
    console.error('[CloudBase] Missing VITE_CLOUDBASE_ENV_ID');
    throw new Error('缺少 VITE_CLOUDBASE_ENV_ID，请先配置 CloudBase 环境 ID');
  }
  cloudApp = cloudbase.init({ env });
  console.info('[CloudBase] SDK initialized:', { env });
  return cloudApp;
}

async function signInAnonymously(app: ReturnType<typeof cloudbase.init>) {
  const auth = app.auth({ persistence: 'local' });

  try {
    const loginState = await auth.getLoginState();
    if (loginState) {
      console.info('[CloudBase] Existing anonymous login state found');
      return;
    }
  } catch (error) {
    console.warn('[CloudBase] Failed to read login state, will try anonymous sign-in:', error);
  }

  try {
    const result = await auth.signInAnonymously();
    const response = result as { error?: unknown };
    if (response?.error) {
      throw response.error;
    }
    console.info('[CloudBase] Anonymous sign-in completed');
  } catch (error) {
    logCloudBaseError('Anonymous sign-in failed', error);
    throw new Error(`CloudBase 匿名登录失败：${getErrorMessage(error)}`);
  }
}

export async function ensureCloudAuth() {
  const app = getCloudApp();
  if (!authReady) {
    authReady = signInAnonymously(app).catch((error) => {
      authReady = null;
      throw error;
    });
  }
  await authReady;
}
