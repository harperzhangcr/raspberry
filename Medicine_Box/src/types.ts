export interface MedicineBatch {
  id: string;
  expiryDate: string;
  quantity: number;
  createdAt: number;
}

export interface Medicine {
  _id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  expiryDate: string;
  batches: MedicineBatch[];
  note?: string;
  location?: string;
  imageUrl?: string;
  deletedAt?: number;
  updatedAt: number;
}

export type MedicineInput = Omit<Medicine, '_id' | 'updatedAt' | 'batches' | 'deletedAt'> & {
  batches?: MedicineBatch[];
};

export type MedicineUpdate = Partial<MedicineInput> & {
  _id: string;
};

export interface MedicineBatchInput {
  expiryDate: string;
  quantity: number;
  createdAt?: number;
}

export type ExpiryStatus = 'expired' | 'expiringSoon' | 'normal';

export type StatusFilter = 'all' | 'inStock' | 'outOfStock' | 'expired' | 'expiringSoon';

export interface MedicineStatus {
  expiryStatus: ExpiryStatus;
  isOutOfStock: boolean;
  labels: Array<{
    text: string;
    type: 'success' | 'warning' | 'danger';
  }>;
}

export interface CategoryGroup {
  category: string;
  medicines: Medicine[];
  hasOutOfStock: boolean;
  hasExpired: boolean;
}
