const CATEGORY_ASSETS: Record<string, string> = {
  发烧止痛: new URL('./assets/categories/fever-pain.webp', import.meta.url).href,
  感冒: new URL('./assets/categories/cold.webp', import.meta.url).href,
  咳嗽: new URL('./assets/categories/cough.webp', import.meta.url).href,
  胃肠道: new URL('./assets/categories/gastrointestinal.webp', import.meta.url).href,
  高血压: new URL('./assets/categories/hypertension.webp', import.meta.url).href,
  高尿酸: new URL('./assets/categories/high-uric-acid.webp', import.meta.url).href,
  高血脂: new URL('./assets/categories/high-lipids.webp', import.meta.url).href,
  皮肤: new URL('./assets/categories/skin.webp', import.meta.url).href,
  皮肤外用: new URL('./assets/categories/skin.webp', import.meta.url).href,
  过敏: new URL('./assets/categories/allergy.webp', import.meta.url).href,
  眼科: new URL('./assets/categories/eye.webp', import.meta.url).href,
  其他: new URL('./assets/categories/other.webp', import.meta.url).href,
};

export function getCategoryAsset(category: string) {
  return CATEGORY_ASSETS[category] || '';
}
