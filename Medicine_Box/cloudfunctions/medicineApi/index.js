const cloudbase = require('@cloudbase/node-sdk');
const { recognizeMedicineByImage } = require('./qwen');

const app = cloudbase.init({
  env: cloudbase.SYMBOL_CURRENT_ENV,
});
const db = app.database();
const _ = db.command;
const collection = db.collection('medicines');

function ok(data) {
  return { success: true, data };
}

function fail(message) {
  return { success: false, message };
}

function requireFamilyCode(familyCode) {
  const expected = process.env.FAMILY_CODE;
  if (!expected) {
    throw new Error('云函数未配置 FAMILY_CODE');
  }
  if (familyCode !== expected) {
    throw new Error('家庭访问码错误');
  }
}

function normalizeMedicine(input) {
  if (!input || typeof input !== 'object') {
    throw new Error('药品数据不能为空');
  }
  const name = String(input.name || '').trim();
  const category = String(input.category || '').trim();
  const unit = String(input.unit || '').trim();
  const expiryDate = String(input.expiryDate || '').trim();
  const quantity = Number(input.quantity);

  if (!name) throw new Error('药名不能为空');
  if (!category) throw new Error('分类不能为空');
  if (!Number.isFinite(quantity) || quantity < 0) throw new Error('数量必须大于等于 0');
  if (!unit) throw new Error('单位不能为空');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(expiryDate)) throw new Error('有效期格式必须为 YYYY-MM-DD');

  const batches = normalizeBatches(input.batches, expiryDate, quantity);
  return syncMedicineFromBatches({
    name,
    category,
    unit,
    quantity,
    expiryDate,
    batches,
    note: String(input.note || '').trim(),
    location: String(input.location || '').trim(),
    imageUrl: String(input.imageUrl || '').trim(),
    dosageTiming: String(input.dosageTiming || '不限').trim() || '不限',
    dosageCycle: String(input.dosageCycle || '').trim(),
  });
}

function createBatch(expiryDate, quantity, createdAt) {
  return {
    id: `batch-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    expiryDate,
    quantity,
    createdAt: Number(createdAt || Date.now()),
  };
}

function normalizeBatchInput(input) {
  if (!input || typeof input !== 'object') throw new Error('库存批次不能为空');
  const expiryDate = String(input.expiryDate || '').trim();
  const quantity = Number(input.quantity);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(expiryDate)) throw new Error('保质期格式必须为 YYYY-MM-DD');
  if (!Number.isFinite(quantity) || quantity <= 0) throw new Error('本次数量必须大于 0');
  return createBatch(expiryDate, quantity, input.createdAt);
}

function normalizeBatches(batches, fallbackExpiryDate, fallbackQuantity) {
  const source = Array.isArray(batches) && batches.length > 0
    ? batches
    : Number(fallbackQuantity) > 0
      ? [createBatch(fallbackExpiryDate, Number(fallbackQuantity))]
      : [];
  const normalized = source
    .map((batch) => ({
      id: String(batch.id || `batch-${Date.now()}-${Math.random().toString(16).slice(2)}`),
      expiryDate: String(batch.expiryDate || fallbackExpiryDate),
      quantity: Number(batch.quantity || 0),
      createdAt: Number(batch.createdAt || Date.now()),
    }))
    .filter((batch) => batch.quantity > 0 && /^\d{4}-\d{2}-\d{2}$/.test(batch.expiryDate));
  const merged = normalized.reduce((result, batch) => {
    const existing = result.get(batch.expiryDate);
    if (!existing) {
      result.set(batch.expiryDate, batch);
      return result;
    }
    result.set(batch.expiryDate, {
      ...existing,
      quantity: existing.quantity + batch.quantity,
      createdAt: Math.min(existing.createdAt, batch.createdAt),
    });
    return result;
  }, new Map());
  return Array.from(merged.values()).sort((a, b) => a.expiryDate.localeCompare(b.expiryDate));
}

function syncMedicineFromBatches(item) {
  const batches = normalizeBatches(item.batches, item.expiryDate, item.quantity);
  const quantity = batches.reduce((sum, batch) => sum + batch.quantity, 0);
  return {
    ...item,
    batches,
    quantity,
    expiryDate: batches[0] ? batches[0].expiryDate : item.expiryDate,
  };
}

function normalizeMedicinePatch(input) {
  const patch = {};
  if (Object.prototype.hasOwnProperty.call(input, 'name')) {
    const name = String(input.name || '').trim();
    if (!name) throw new Error('药名不能为空');
    patch.name = name;
  }
  if (Object.prototype.hasOwnProperty.call(input, 'category')) {
    const category = String(input.category || '').trim();
    if (!category) throw new Error('分类不能为空');
    patch.category = category;
  }
  if (Object.prototype.hasOwnProperty.call(input, 'quantity')) {
    const quantity = Number(input.quantity);
    if (!Number.isFinite(quantity) || quantity < 0) throw new Error('数量必须大于等于 0');
    patch.quantity = quantity;
  }
  if (Object.prototype.hasOwnProperty.call(input, 'unit')) {
    const unit = String(input.unit || '').trim();
    if (!unit) throw new Error('单位不能为空');
    patch.unit = unit;
  }
  if (Object.prototype.hasOwnProperty.call(input, 'expiryDate')) {
    const expiryDate = String(input.expiryDate || '').trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(expiryDate)) throw new Error('有效期格式必须为 YYYY-MM-DD');
    patch.expiryDate = expiryDate;
  }
  if (Object.prototype.hasOwnProperty.call(input, 'note')) {
    patch.note = String(input.note || '').trim();
  }
  if (Object.prototype.hasOwnProperty.call(input, 'location')) {
    patch.location = String(input.location || '').trim();
  }
  if (Object.prototype.hasOwnProperty.call(input, 'imageUrl')) {
    patch.imageUrl = String(input.imageUrl || '').trim();
  }
  if (Object.prototype.hasOwnProperty.call(input, 'dosageTiming')) {
    patch.dosageTiming = String(input.dosageTiming || '不限').trim() || '不限';
  }
  if (Object.prototype.hasOwnProperty.call(input, 'dosageCycle')) {
    patch.dosageCycle = String(input.dosageCycle || '').trim();
  }
  return patch;
}

function stripCreatedAt(item) {
  if (!item) return item;
  const { createdAt, ...rest } = item;
  return syncMedicineFromBatches(rest);
}

function isDeletedMedicine(item) {
  return Number(item && item.deletedAt ? item.deletedAt : 0) > 0;
}

function normalizeMedicineName(name) {
  return String(name || '').trim().toLowerCase();
}

async function listMedicines() {
  const result = await collection.orderBy('category', 'asc').orderBy('name', 'asc').get();
  return (result.data || [])
    .filter((item) => !isDeletedMedicine(item))
    .map(stripCreatedAt);
}

async function findExistingMedicineByName(name, excludedId) {
  const normalizedName = normalizeMedicineName(name);
  const result = await collection.get();
  return (result.data || []).find(
    (item) => item._id !== excludedId && !isDeletedMedicine(item) && normalizeMedicineName(item.name) === normalizedName,
  );
}

function getEmptyFieldSupplements(existing, incoming) {
  const supplement = {};
  if (!String(existing.imageUrl || '').trim() && String(incoming && incoming.imageUrl || '').trim()) {
    supplement.imageUrl = String(incoming.imageUrl).trim();
  }
  if (!String(existing.location || '').trim() && String(incoming && incoming.location || '').trim()) {
    supplement.location = String(incoming.location).trim();
  }
  if (!String(existing.note || '').trim() && String(incoming && incoming.note || '').trim()) {
    supplement.note = String(incoming.note).trim();
  }
  if (!String(existing.dosageTiming || '').trim() && String(incoming && incoming.dosageTiming || '').trim()) {
    supplement.dosageTiming = String(incoming.dosageTiming).trim();
  }
  if (!String(existing.dosageCycle || '').trim() && String(incoming && incoming.dosageCycle || '').trim()) {
    supplement.dosageCycle = String(incoming.dosageCycle).trim();
  }
  return supplement;
}

async function appendBatchToMedicine(id, batch, supplementsSource) {
  const current = await collection.doc(id).get();
  const item = current.data && current.data[0];
  if (!item) throw new Error('未找到药品');
  const synced = syncMedicineFromBatches(item);
  const supplements = getEmptyFieldSupplements(synced, supplementsSource);
  const next = syncMedicineFromBatches({ ...synced, ...supplements, batches: [...synced.batches, batch] });
  const updatedAt = Date.now();
  await collection.doc(id).update({
    batches: next.batches,
    quantity: next.quantity,
    expiryDate: next.expiryDate,
    ...supplements,
    updatedAt,
    createdAt: _.remove(),
  });
  return stripCreatedAt({ ...next, updatedAt });
}

async function listDeletedMedicines() {
  const result = await collection.get();
  return (result.data || [])
    .filter(isDeletedMedicine)
    .sort((a, b) => Number(b.deletedAt || 0) - Number(a.deletedAt || 0))
    .map(stripCreatedAt);
}

async function resolveCloudImageUrl(imageUrl) {
  const value = String(imageUrl || '').trim();
  console.log('[aiRecognizeMedicine] resolve imageUrl exists:', Boolean(value));
  console.log('[aiRecognizeMedicine] resolve imageUrl type/prefix:', {
    type: typeof imageUrl,
    prefix: value.slice(0, 16),
  });
  if (!value) throw new Error('图片不能为空');
  if (!value.startsWith('cloud://')) {
    console.log('[aiRecognizeMedicine] getTempFileURL skipped: non-cloud URL');
    return value;
  }

  console.log('[aiRecognizeMedicine] getTempFileURL start');
  const result = await app.getTempFileURL({
    fileList: [value],
  });
  console.log('[aiRecognizeMedicine] getTempFileURL result:', {
    hasFileList: Array.isArray(result.fileList),
    firstStatus: result.fileList && result.fileList[0] && result.fileList[0].status,
    firstCode: result.fileList && result.fileList[0] && result.fileList[0].code,
    firstMessage: result.fileList && result.fileList[0] && result.fileList[0].message,
  });
  const tempUrl = result.fileList && result.fileList[0] && result.fileList[0].tempFileURL;
  if (!tempUrl) throw new Error('图片地址无效');
  return tempUrl;
}

exports.main = async (event) => {
  try {
    const { action, familyCode } = event || {};

    requireFamilyCode(familyCode);

    if (action === 'list') {
      return ok(await listMedicines());
    }

    if (action === 'listDeleted') {
      return ok(await listDeletedMedicines());
    }

    if (action === 'findByName') {
      const name = String(event.name || '').trim();
      if (!name) return ok(null);
      const medicine = await findExistingMedicineByName(name);
      return ok(medicine ? stripCreatedAt(medicine) : null);
    }

    if (action === 'aiRecognizeMedicine') {
      try {
        console.log('[aiRecognizeMedicine] action entered');
        console.log('[aiRecognizeMedicine] received imageUrl:', {
          exists: Boolean(event.imageUrl),
          type: typeof event.imageUrl,
          prefix: String(event.imageUrl || '').slice(0, 16),
        });
        const imageUrl = await resolveCloudImageUrl(event.imageUrl);
        console.log('[aiRecognizeMedicine] image URL for Qwen prefix:', imageUrl.slice(0, 80));
        return ok(await recognizeMedicineByImage(imageUrl));
      } catch (error) {
        console.error('[aiRecognizeMedicine] failed message:', error.message);
        console.error('[aiRecognizeMedicine] failed stack:', error.stack);
        return ok({
          error: true,
          message: error.message === 'AI识别结果格式异常' ? 'AI识别结果格式异常' : 'AI识别失败',
        });
      }
    }

    if (action === 'add') {
      const now = Date.now();
      const medicine = {
        ...normalizeMedicine(event.medicine),
        updatedAt: now,
      };
      const existing = await findExistingMedicineByName(medicine.name);
      if (existing) {
        if (medicine.quantity <= 0) {
          const supplements = getEmptyFieldSupplements(existing, medicine);
          if (Object.keys(supplements).length > 0) {
            const updatedAt = Date.now();
            await collection.doc(existing._id).update({ ...supplements, updatedAt, createdAt: _.remove() });
            return ok(stripCreatedAt({ ...existing, ...supplements, updatedAt }));
          }
          return ok(stripCreatedAt(existing));
        }
        return ok(await appendBatchToMedicine(existing._id, createBatch(medicine.expiryDate, medicine.quantity), medicine));
      }
      const result = await collection.add(medicine);
      return ok({ ...medicine, _id: result.id });
    }

    if (action === 'update') {
      const medicine = event.medicine || {};
      if (!medicine._id) throw new Error('缺少药品 ID');
      const patch = normalizeMedicinePatch(medicine);
      if (Object.prototype.hasOwnProperty.call(patch, 'name')) {
        const duplicate = await findExistingMedicineByName(patch.name, medicine._id);
        if (duplicate) throw new Error('已存在同名药品，不能重复创建');
      }
      const batchPatch = Object.prototype.hasOwnProperty.call(patch, 'quantity') || Object.prototype.hasOwnProperty.call(patch, 'expiryDate')
        ? syncMedicineFromBatches({
            batches: normalizeBatches([], patch.expiryDate || medicine.expiryDate, patch.quantity || 0),
            quantity: patch.quantity || 0,
            expiryDate: patch.expiryDate || medicine.expiryDate,
          })
        : {};
      const updateData = {
        ...patch,
        ...batchPatch,
        updatedAt: Date.now(),
        createdAt: _.remove(),
      };
      await collection.doc(medicine._id).update(updateData);
      const latest = await collection.doc(medicine._id).get();
      return ok(latest.data && latest.data[0] ? stripCreatedAt(latest.data[0]) : stripCreatedAt({ _id: medicine._id, ...updateData }));
    }

    if (action === 'delete') {
      if (!event.id) throw new Error('缺少药品 ID');
      const now = Date.now();
      await collection.doc(event.id).update({
        deletedAt: now,
        updatedAt: now,
        createdAt: _.remove(),
      });
      return ok(true);
    }

    if (action === 'restore') {
      if (!event.id) throw new Error('缺少药品 ID');
      const updatedAt = Date.now();
      await collection.doc(event.id).update({
        deletedAt: _.remove(),
        updatedAt,
        createdAt: _.remove(),
      });
      const latest = await collection.doc(event.id).get();
      return ok(latest.data && latest.data[0] ? stripCreatedAt(latest.data[0]) : stripCreatedAt({ _id: event.id, updatedAt }));
    }

    if (action === 'permanentDelete') {
      if (!event.id) throw new Error('缺少药品 ID');
      await collection.doc(event.id).remove();
      return ok(true);
    }

    if (action === 'adjustQuantity') {
      if (!event.id) throw new Error('缺少药品 ID');
      const delta = Number(event.delta);
      if (delta !== -1 && delta !== 1) throw new Error('库存调整值只能是 -1 或 1');
      const current = await collection.doc(event.id).get();
      const item = current.data && current.data[0];
      if (!item) throw new Error('未找到药品');
      const synced = syncMedicineFromBatches(item);
      const batches = [...synced.batches];
      if (batches.length === 0) {
        if (delta === -1) throw new Error('库存已为 0');
        if (!/^\d{4}-\d{2}-\d{2}$/.test(String(synced.expiryDate || ''))) {
          throw new Error('缺少有效期，无法创建库存批次');
        }
        batches.push({
          id: `batch-${Date.now()}-${Math.random().toString(16).slice(2)}`,
          expiryDate: synced.expiryDate,
          quantity: 0,
          createdAt: Date.now(),
        });
      }
      batches[0].quantity = Math.max(0, batches[0].quantity + delta);
      const next = syncMedicineFromBatches({ ...synced, batches });
      const updatedAt = Date.now();
      await collection.doc(event.id).update({ batches: next.batches, quantity: next.quantity, expiryDate: next.expiryDate, updatedAt, createdAt: _.remove() });
      return ok(stripCreatedAt({ ...next, updatedAt }));
    }

    if (action === 'addBatch') {
      if (!event.id) throw new Error('缺少药品 ID');
      return ok(await appendBatchToMedicine(event.id, normalizeBatchInput(event.batch)));
    }

    if (action === 'updateBatch') {
      if (!event.id) throw new Error('缺少药品 ID');
      const batchId = String(event.batchId || '').trim();
      if (!batchId) throw new Error('缺少库存批次 ID');
      const batchPatch = normalizeBatchInput(event.batch);
      const current = await collection.doc(event.id).get();
      const item = current.data && current.data[0];
      if (!item) throw new Error('未找到药品');
      const synced = syncMedicineFromBatches(item);
      const target = synced.batches.find((batch) => batch.id === batchId);
      if (!target) throw new Error('未找到库存批次');
      const next = syncMedicineFromBatches({
        ...synced,
        batches: synced.batches.map((batch) =>
          batch.id === batchId
            ? {
                ...batch,
                expiryDate: batchPatch.expiryDate,
                quantity: batchPatch.quantity,
                createdAt: batchPatch.createdAt || batch.createdAt,
              }
            : batch,
        ),
      });
      const updatedAt = Date.now();
      await collection.doc(event.id).update({
        batches: next.batches,
        quantity: next.quantity,
        expiryDate: next.expiryDate,
        updatedAt,
        createdAt: _.remove(),
      });
      return ok(stripCreatedAt({ ...next, updatedAt }));
    }

    if (action === 'deleteBatch') {
      if (!event.id) throw new Error('缺少药品 ID');
      const batchId = String(event.batchId || '').trim();
      if (!batchId) throw new Error('缺少库存批次 ID');
      const current = await collection.doc(event.id).get();
      const item = current.data && current.data[0];
      if (!item) throw new Error('未找到药品');
      const synced = syncMedicineFromBatches(item);
      const nextBatches = synced.batches.filter((batch) => batch.id !== batchId);
      if (nextBatches.length === synced.batches.length) throw new Error('未找到库存批次');
      const nextQuantity = nextBatches.reduce((sum, batch) => sum + batch.quantity, 0);
      const next = syncMedicineFromBatches({
        ...synced,
        batches: nextBatches,
        quantity: nextQuantity,
        expiryDate: nextBatches[0] ? nextBatches[0].expiryDate : synced.expiryDate,
      });
      const updatedAt = Date.now();
      await collection.doc(event.id).update({
        batches: next.batches,
        quantity: next.quantity,
        expiryDate: next.expiryDate,
        updatedAt,
        createdAt: _.remove(),
      });
      return ok(stripCreatedAt({ ...next, updatedAt }));
    }

    return fail('未知 action');
  } catch (error) {
    return fail(error.message || '云函数执行失败');
  }
};
