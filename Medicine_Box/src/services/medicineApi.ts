import { DATA_MODE } from '../constants';
import { mockMedicines } from './mockData';
import type { Medicine, MedicineBatch, MedicineBatchInput, MedicineInput, MedicineUpdate } from '../types';
import { normalizeMedicineBatches, sortBatches } from '../utils/medicine';
import { ensureCloudAuth, getCloudApp, logCloudBaseError } from './cloudbaseClient';

let localMedicines: Medicine[] = [...mockMedicines];

function assertSuccess(result: unknown) {
  const response = result as { result?: { success?: boolean; message?: string; data?: unknown } };
  if (!response.result?.success) {
    console.error('[CloudBase] medicineApi returned failure:', result);
    throw new Error(response.result?.message || '操作失败');
  }
  return response.result.data;
}

async function callMedicineApi<T>(action: string, payload: Record<string, unknown> = {}): Promise<T> {
  const app = getCloudApp();
  await ensureCloudAuth();
  try {
    const result = await app.callFunction({
      name: 'medicineApi',
      data: {
        action,
        ...payload,
      },
    });
    return assertSuccess(result) as T;
  } catch (error) {
    logCloudBaseError(`medicineApi action "${action}" failed`, error);
    throw error;
  }
}

function mockDelay<T>(data: T) {
  return new Promise<T>((resolve) => {
    window.setTimeout(() => resolve(data), 180);
  });
}

function createBatch(expiryDate: string, quantity: number): MedicineBatch {
  return {
    id: `batch-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    expiryDate,
    quantity,
    createdAt: Date.now(),
  };
}

function syncMedicineFromBatches(medicine: Medicine): Medicine {
  return normalizeMedicineBatches(medicine);
}

function isDeletedMedicine(medicine: Medicine) {
  return Number(medicine.deletedAt || 0) > 0;
}

function normalizeMedicineName(name: string) {
  return name.trim().toLowerCase();
}

function findExistingMedicineByName(name: string) {
  const normalizedName = normalizeMedicineName(name);
  return localMedicines.find(
    (item) => !isDeletedMedicine(item) && normalizeMedicineName(item.name) === normalizedName,
  );
}

function withEmptyFieldSupplements(existing: Medicine, incoming: MedicineInput): Medicine {
  return {
    ...existing,
    imageUrl: existing.imageUrl?.trim() ? existing.imageUrl : incoming.imageUrl?.trim() || existing.imageUrl,
    location: existing.location?.trim() ? existing.location : incoming.location?.trim() || existing.location,
    note: existing.note?.trim() ? existing.note : incoming.note?.trim() || existing.note,
  };
}

export const medicineApi = {
  async verifyFamilyCode(familyCode: string) {
    if (DATA_MODE === 'mock') {
      return mockDelay(familyCode.trim().length > 0);
    }
    await callMedicineApi<boolean>('list', { familyCode });
    return true;
  },

  async list(familyCode: string) {
    if (DATA_MODE === 'mock') {
      localMedicines = localMedicines.map(syncMedicineFromBatches);
      return mockDelay(localMedicines.filter((item) => !isDeletedMedicine(item)));
    }
    const medicines = await callMedicineApi<Medicine[]>('list', { familyCode });
    return medicines.map(syncMedicineFromBatches);
  },

  async listDeletedMedicines(familyCode: string) {
    if (DATA_MODE === 'mock') {
      localMedicines = localMedicines.map(syncMedicineFromBatches);
      const deletedMedicines = localMedicines
        .filter(isDeletedMedicine)
        .sort((a, b) => Number(b.deletedAt || 0) - Number(a.deletedAt || 0));
      return mockDelay(deletedMedicines);
    }
    const medicines = await callMedicineApi<Medicine[]>('listDeleted', { familyCode });
    return medicines.map(syncMedicineFromBatches);
  },

  async findByName(familyCode: string, name: string) {
    const normalizedName = normalizeMedicineName(name);
    if (!normalizedName) return null;
    if (DATA_MODE === 'mock') {
      localMedicines = localMedicines.map(syncMedicineFromBatches);
      const medicine = localMedicines.find(
        (item) => !isDeletedMedicine(item) && normalizeMedicineName(item.name) === normalizedName,
      );
      return mockDelay(medicine || null);
    }
    const medicine = await callMedicineApi<Medicine | null>('findByName', { familyCode, name });
    return medicine ? syncMedicineFromBatches(medicine) : null;
  },

  async add(familyCode: string, medicine: MedicineInput) {
    if (DATA_MODE === 'mock') {
      const now = Date.now();
      const existing = findExistingMedicineByName(medicine.name);
      if (existing) {
        let updated: Medicine | undefined;
        localMedicines = localMedicines.map((item) => {
          if (item._id !== existing._id) return item;
          const normalized = withEmptyFieldSupplements(syncMedicineFromBatches(item), medicine);
          updated = syncMedicineFromBatches({
            ...normalized,
            batches:
              medicine.quantity > 0
                ? [...normalized.batches, createBatch(medicine.expiryDate, medicine.quantity)]
                : normalized.batches,
            updatedAt: now,
          });
          return updated;
        });
        return mockDelay(updated || existing);
      }
      const batches = medicine.quantity > 0 ? [createBatch(medicine.expiryDate, medicine.quantity)] : [];
      const item: Medicine = {
        ...medicine,
        _id: `mock-${now}`,
        batches,
        updatedAt: now,
      };
      const normalized = syncMedicineFromBatches(item);
      localMedicines = [normalized, ...localMedicines];
      return mockDelay(normalized);
    }
    return callMedicineApi<Medicine>('add', { familyCode, medicine });
  },

  async update(familyCode: string, medicine: MedicineUpdate) {
    if (DATA_MODE === 'mock') {
      const duplicate = medicine.name
        ? localMedicines.find(
            (item) =>
              item._id !== medicine._id &&
              !isDeletedMedicine(item) &&
              normalizeMedicineName(item.name) === normalizeMedicineName(medicine.name || ''),
          )
        : undefined;
      if (duplicate) throw new Error('已存在同名药品，不能重复创建');

      let updated: Medicine | undefined;
      localMedicines = localMedicines.map((item) => {
        if (item._id !== medicine._id) return item;
        const nextBatches =
          typeof medicine.quantity === 'number' || medicine.expiryDate
            ? medicine.quantity && medicine.quantity > 0
              ? [createBatch(medicine.expiryDate || item.expiryDate, medicine.quantity)]
              : []
            : item.batches;
        updated = syncMedicineFromBatches({ ...item, ...medicine, batches: nextBatches, updatedAt: Date.now() });
        return updated;
      });
      if (!updated) throw new Error('未找到药品');
      return mockDelay(updated);
    }
    return callMedicineApi<Medicine>('update', { familyCode, medicine });
  },

  async delete(familyCode: string, id: string) {
    if (DATA_MODE === 'mock') {
      const now = Date.now();
      localMedicines = localMedicines.map((item) =>
        item._id === id ? { ...item, deletedAt: now, updatedAt: now } : item,
      );
      return mockDelay(true);
    }
    return callMedicineApi<boolean>('delete', { familyCode, id });
  },

  async restoreMedicine(familyCode: string, id: string) {
    if (DATA_MODE === 'mock') {
      let restored: Medicine | undefined;
      localMedicines = localMedicines.map((item) => {
        if (item._id !== id) return item;
        restored = { ...item, updatedAt: Date.now() };
        delete restored.deletedAt;
        return syncMedicineFromBatches(restored);
      });
      if (!restored) throw new Error('未找到药品');
      return mockDelay(syncMedicineFromBatches(restored));
    }
    const medicine = await callMedicineApi<Medicine>('restore', { familyCode, id });
    return syncMedicineFromBatches(medicine);
  },

  async permanentDeleteMedicine(familyCode: string, id: string) {
    if (DATA_MODE === 'mock') {
      localMedicines = localMedicines.filter((item) => item._id !== id);
      return mockDelay(true);
    }
    return callMedicineApi<boolean>('permanentDelete', { familyCode, id });
  },

  async adjustQuantity(familyCode: string, id: string, delta: -1 | 1) {
    if (DATA_MODE === 'mock') {
      let updated: Medicine | undefined;
      localMedicines = localMedicines.map((item) => {
        if (item._id !== id) return item;
        const normalized = syncMedicineFromBatches(item);
        const batches = sortBatches(normalized.batches);
        if (batches.length === 0) {
          if (delta === -1) throw new Error('库存已为 0');
          batches.push(createBatch(normalized.expiryDate, 0));
        }
        batches[0] = { ...batches[0], quantity: Math.max(0, batches[0].quantity + delta) };
        updated = {
          ...normalized,
          batches: sortBatches(batches),
          updatedAt: Date.now(),
        };
        return syncMedicineFromBatches(updated);
      });
      if (!updated) throw new Error('未找到药品');
      return mockDelay(updated);
    }
    return callMedicineApi<Medicine>('adjustQuantity', { familyCode, id, delta });
  },

  async addBatch(familyCode: string, id: string, batch: MedicineBatchInput) {
    if (DATA_MODE === 'mock') {
      let updated: Medicine | undefined;
      localMedicines = localMedicines.map((item) => {
        if (item._id !== id) return item;
        const normalized = syncMedicineFromBatches(item);
        updated = syncMedicineFromBatches({
          ...normalized,
          batches: [
            ...normalized.batches,
            batch.createdAt
              ? { ...createBatch(batch.expiryDate, batch.quantity), createdAt: batch.createdAt }
              : createBatch(batch.expiryDate, batch.quantity),
          ],
          updatedAt: Date.now(),
        });
        return updated;
      });
      if (!updated) throw new Error('未找到药品');
      return mockDelay(updated);
    }
    return callMedicineApi<Medicine>('addBatch', { familyCode, id, batch });
  },
};
