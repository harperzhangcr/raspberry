import type { CategoryGroup, Medicine, MedicineBatch, MedicineStatus, StatusFilter } from '../types';
import { DEFAULT_CATEGORIES } from '../constants';

const DAY_MS = 24 * 60 * 60 * 1000;

export function todayDateString() {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function toLocalDate(dateString: string) {
  return new Date(`${dateString}T00:00:00`);
}

export function sortBatches(batches: MedicineBatch[]) {
  return [...batches]
    .filter((batch) => batch.quantity > 0)
    .sort((a, b) => a.expiryDate.localeCompare(b.expiryDate));
}

export function mergeBatchesByExpiryDate(batches: MedicineBatch[]) {
  const merged = new Map<string, MedicineBatch>();

  batches
    .filter((batch) => batch.quantity > 0)
    .forEach((batch) => {
      const normalizedBatch = {
        ...batch,
        createdAt: batch.createdAt || Date.now(),
      };
      const existing = merged.get(batch.expiryDate);
      if (!existing) {
        merged.set(batch.expiryDate, normalizedBatch);
        return;
      }
      merged.set(batch.expiryDate, {
        ...existing,
        quantity: existing.quantity + normalizedBatch.quantity,
        createdAt: Math.min(existing.createdAt, normalizedBatch.createdAt),
      });
    });

  return sortBatches(Array.from(merged.values()));
}

export function normalizeMedicineBatches(medicine: Medicine): Medicine {
  const sourceBatches =
    Array.isArray(medicine.batches) && medicine.batches.length > 0
      ? medicine.batches
      : medicine.quantity > 0
        ? [
            {
              id: `${medicine._id || 'legacy'}-${medicine.expiryDate}`,
              expiryDate: medicine.expiryDate,
              quantity: medicine.quantity,
              createdAt: medicine.updatedAt,
            },
          ]
        : [];
  const batches = mergeBatchesByExpiryDate(sourceBatches);
  const quantity = batches.reduce((sum, batch) => sum + batch.quantity, 0);
  return {
    ...medicine,
    batches,
    quantity,
    expiryDate: batches[0]?.expiryDate || medicine.expiryDate,
  };
}

export function getMedicineStatus(medicine: Medicine): MedicineStatus {
  const normalized = normalizeMedicineBatches(medicine);
  const today = toLocalDate(todayDateString());
  const expiry = toLocalDate(normalized.expiryDate);
  const daysLeft = Math.ceil((expiry.getTime() - today.getTime()) / DAY_MS);
  const isOutOfStock = normalized.quantity === 0;
  const expiryStatus = daysLeft < 0 ? 'expired' : daysLeft <= 30 ? 'expiringSoon' : 'normal';
  const labels: MedicineStatus['labels'] = [];

  if (isOutOfStock) {
    labels.push({ text: '缺货', type: 'danger' });
  }
  if (expiryStatus === 'expired') {
    labels.push({ text: '已过期', type: 'danger' });
  } else if (expiryStatus === 'expiringSoon') {
    labels.push({ text: '30天内过期', type: 'warning' });
  }
  return { expiryStatus, isOutOfStock, labels };
}

export function sortMedicines(medicines: Medicine[]) {
  return [...medicines].sort((a, b) => {
    const categoryOrder = a.category.localeCompare(b.category, 'zh-Hans-CN');
    if (categoryOrder !== 0) return categoryOrder;
    return a.name.localeCompare(b.name, 'zh-Hans-CN');
  });
}

export function filterMedicines(
  medicines: Medicine[],
  keyword: string,
  category: string,
  status: StatusFilter,
) {
  const trimmed = keyword.trim();
  return sortMedicines(medicines).filter((medicine) => {
    const itemStatus = getMedicineStatus(medicine);
    const matchKeyword = !trimmed || medicine.name.includes(trimmed);
    const matchCategory = category === '全部' || medicine.category === category;
    const matchStatus =
      status === 'all' ||
      (status === 'inStock' && !itemStatus.isOutOfStock && itemStatus.expiryStatus !== 'expired') ||
      (status === 'outOfStock' && itemStatus.isOutOfStock) ||
      (status === 'expired' && itemStatus.expiryStatus === 'expired') ||
      (status === 'expiringSoon' && itemStatus.expiryStatus === 'expiringSoon');

    return matchKeyword && matchCategory && matchStatus;
  });
}

export function getCategories(medicines: Medicine[], customCategories: string[]) {
  return Array.from(new Set([...DEFAULT_CATEGORIES, ...customCategories, ...medicines.map((item) => item.category)]));
}

export function groupByCategory(medicines: Medicine[], categories: string[]): CategoryGroup[] {
  return categories
    .map((category) => {
      const items = sortMedicines(medicines.filter((item) => item.category === category));
      return {
        category,
        medicines: items,
        hasOutOfStock: items.some((item) => getMedicineStatus(item).isOutOfStock),
        hasExpired: items.some((item) => getMedicineStatus(item).expiryStatus === 'expired'),
      };
    })
    .filter((group) => group.medicines.length > 0);
}

export function formatDateTime(timestamp: number) {
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}
