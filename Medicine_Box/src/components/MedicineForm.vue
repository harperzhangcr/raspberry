<template>
  <section class="form-panel">
    <div class="form-panel__header">
      <div>
        <p class="eyebrow">{{ medicine ? 'Edit Medicine' : 'New Medicine' }}</p>
        <h2>{{ medicine ? '编辑药品' : '新增药品' }}</h2>
      </div>
      <van-button icon="cross" size="small" plain aria-label="关闭表单" @click="$emit('cancel')" />
    </div>

    <van-form class="medicine-form" @submit="submit">
      <section class="form-card">
        <van-field
          v-model="form.name"
          name="name"
          label="药名"
          placeholder="例如：布洛芬"
          :readonly="isNameLocked"
          :rules="[{ required: true, message: '请输入药名' }]"
        />
        <van-field
          v-model="form.category"
          is-link
          readonly
          name="category"
          label="分类"
          placeholder="请选择分类"
          :rules="[{ required: true, message: '请选择分类' }]"
          @click="showCategoryPicker = true"
        />
      </section>

      <section class="form-card form-card--grid">
        <van-field
          v-model.number="form.quantity"
          type="number"
          name="quantity"
          label="数量"
          placeholder="0"
          :rules="[{ required: true, message: '请输入数量' }]"
        />
        <van-field
          v-model="form.unit"
          name="unit"
          label="单位"
          placeholder="盒、瓶、板、袋"
          :rules="[{ required: true, message: '请输入单位' }]"
        />
      </section>

      <section class="form-card">
        <van-field
          v-model="form.expiryDate"
          type="date"
          name="expiryDate"
          label="有效期"
          :rules="[{ required: true, message: '请选择有效期' }]"
        />
        <van-field
          v-model="form.note"
          rows="3"
          autosize
          type="textarea"
          name="note"
          label="备注"
          placeholder="例如：儿童用、饭后服、需冷藏"
        />
      </section>

      <section class="form-card">
        <van-field
          v-model="form.location"
          name="location"
          label="存放位置"
          placeholder="例如 药箱1 / 客厅抽屉 / 冰箱"
        />
        <div class="photo-field">
          <div class="photo-field__label">药品照片</div>
          <div class="photo-field__body">
            <van-uploader
              v-model="imageFileList"
              accept="image/*"
              image-fit="cover"
              reupload
              :after-read="handleImageRead"
              :before-delete="handleImageDelete"
              :max-count="1"
              :preview-size="[88, 88]"
              upload-icon="photograph"
              upload-text="上传/拍照"
            />
          </div>
        </div>
      </section>

      <div class="form-save-bar">
        <van-button block type="primary" native-type="submit">保存</van-button>
      </div>
    </van-form>

    <van-popup v-model:show="showCategoryPicker" position="bottom" round>
      <van-picker
        title="选择分类"
        :columns="categoryColumns"
        @confirm="onCategoryConfirm"
        @cancel="showCategoryPicker = false"
      />
    </van-popup>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { showFailToast } from 'vant';
import type { UploaderFileListItem } from 'vant';
import type { AiMedicineRecognition, Medicine, MedicineInput } from '../types';
import { resolveMedicineImageUrl, uploadMedicineImage } from '../services/medicineStorage';
import { todayDateString } from '../utils/medicine';

const props = defineProps<{
  medicine: Medicine | null;
  categories: string[];
  findMedicineByName?: (name: string) => Promise<Medicine | null>;
  recognizeMedicineImage?: (imageUrl: string) => Promise<AiMedicineRecognition>;
}>();

const emit = defineEmits<{
  cancel: [];
  submit: [payload: MedicineInput, matchedMedicine: Medicine | null];
}>();

const showCategoryPicker = ref(false);
const imageFileList = ref<UploaderFileListItem[]>([]);
const matchedMedicine = ref<Medicine | null>(null);
const form = reactive<MedicineInput>({
  name: '',
  category: '',
  quantity: 1,
  unit: '盒',
  expiryDate: todayDateString(),
  note: '',
  location: '',
  imageUrl: '',
});

const categoryColumns = computed(() => props.categories.map((category) => ({ text: category, value: category })));
const isNameLocked = computed(() => !props.medicine && !!matchedMedicine.value);
let imagePreviewRequestId = 0;
let nameLookupRequestId = 0;
let nameLookupTimer: number | undefined;
let aiRecognitionRequestId = 0;

async function syncImagePreview(imageUrl?: string) {
  const requestId = ++imagePreviewRequestId;
  const value = String(imageUrl || '').trim();
  if (!value) {
    imageFileList.value = [];
    return;
  }
  const previewUrl = await resolveMedicineImageUrl(value);
  if (requestId !== imagePreviewRequestId) return;
  imageFileList.value = [
    {
      url: previewUrl || value,
      isImage: true,
      status: 'done',
    },
  ];
}

watch(
  () => props.medicine,
  (medicine) => {
    matchedMedicine.value = null;
    form.name = medicine?.name || '';
    form.category = medicine?.category || props.categories[0] || '';
    form.quantity = medicine ? medicine.quantity : 1;
    form.unit = medicine?.unit || '盒';
    form.expiryDate = medicine?.expiryDate || todayDateString();
    form.note = medicine?.note || '';
    form.location = medicine?.location || '';
    form.imageUrl = medicine?.imageUrl || '';
    void syncImagePreview(medicine?.imageUrl);
  },
  { immediate: true },
);

watch(
  () => form.name,
  (name) => {
    if (props.medicine || matchedMedicine.value) return;
    if (nameLookupTimer) {
      window.clearTimeout(nameLookupTimer);
    }
    nameLookupTimer = window.setTimeout(() => {
      void lookupExistingMedicine(name);
    }, 260);
  },
);

async function lookupExistingMedicine(name: string) {
  const trimmedName = name.trim();
  const requestId = ++nameLookupRequestId;
  if (!trimmedName || !props.findMedicineByName) {
    matchedMedicine.value = null;
    return;
  }

  try {
    const existing = await props.findMedicineByName(trimmedName);
    if (requestId !== nameLookupRequestId || !existing) return;
    matchedMedicine.value = existing;
    form.name = existing.name;
    form.category = existing.category;
    form.unit = existing.unit;
    form.note = existing.note || '';
    form.location = existing.location || '';
    form.imageUrl = existing.imageUrl || '';
    void syncImagePreview(existing.imageUrl);
  } catch {
    if (requestId === nameLookupRequestId) {
      showFailToast('同名药品查询失败');
    }
  }
}

function normalizeRecognizedCategory(category: string) {
  const value = category.trim();
  if (!value) return '';
  return props.categories.includes(value) ? value : '其他';
}

function applyRecognitionResult(result: AiMedicineRecognition) {
  if (props.medicine || matchedMedicine.value) return;
  if (result.name.trim()) {
    form.name = result.name.trim();
  }
  const category = normalizeRecognizedCategory(result.category);
  if (category) {
    form.category = category;
  }
  if (result.indications.trim()) {
    form.note = result.indications.trim();
  }
}

async function recognizeUploadedImage(imageUrl: string) {
  if (!props.recognizeMedicineImage) return;
  const requestId = ++aiRecognitionRequestId;

  try {
    const result = await props.recognizeMedicineImage(imageUrl);
    if (requestId !== aiRecognitionRequestId) return;
    applyRecognitionResult(result);
  } catch {
    if (requestId === aiRecognitionRequestId) {
      showFailToast('AI识别失败，可手动填写');
    }
  }
}

function onCategoryConfirm(event: { selectedOptions: Array<{ text: string; value: string }> }) {
  form.category = event.selectedOptions[0]?.value || '';
  showCategoryPicker.value = false;
}

async function handleImageRead(item: UploaderFileListItem | UploaderFileListItem[]) {
  const fileItem = Array.isArray(item) ? item[0] : item;
  if (!fileItem?.file) return;

  fileItem.status = 'uploading';
  fileItem.message = '上传中';

  try {
    const imageUrl = await uploadMedicineImage(fileItem.file);
    form.imageUrl = imageUrl;
    const previewUrl = await resolveMedicineImageUrl(imageUrl);
    imageFileList.value = [
      {
        url: previewUrl || fileItem.objectUrl || fileItem.content,
        isImage: true,
        status: 'done',
      },
    ];
    void recognizeUploadedImage(imageUrl);
  } catch {
    fileItem.status = 'failed';
    fileItem.message = '上传失败';
    showFailToast('图片上传失败，仍可保存药品信息');
  }
}

function handleImageDelete() {
  aiRecognitionRequestId += 1;
  form.imageUrl = '';
  imageFileList.value = [];
  return true;
}

function submit() {
  emit('submit', {
    name: form.name.trim(),
    category: form.category,
    quantity: Math.max(0, Number(form.quantity) || 0),
    unit: form.unit.trim(),
    expiryDate: form.expiryDate,
    note: form.note?.trim(),
    location: form.location?.trim(),
    imageUrl: form.imageUrl?.trim(),
  }, matchedMedicine.value);
}
</script>

<style scoped>
.form-panel {
  min-height: min(74vh, 680px);
  padding: var(--space-lg) var(--space-md) 0;
  background: var(--color-bg);
}

.form-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.form-panel__header h2 {
  margin: 0;
  color: var(--color-text);
  font-size: var(--font-size-xl);
  line-height: var(--line-tight);
}

.medicine-form {
  display: grid;
  gap: var(--space-md);
  padding-bottom: calc(92px + var(--safe-bottom));
}

.form-card {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-card-solid);
  box-shadow: var(--shadow-card);
}

.form-card--grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
}

.form-card--grid :deep(.van-cell:first-child) {
  border-right: 1px solid var(--color-border);
}

.form-card :deep(.van-field) {
  min-height: 56px;
  align-items: center;
  padding: 14px var(--space-md);
}

.form-card :deep(.van-field__label) {
  display: flex;
  align-items: center;
  width: 70px;
  color: var(--color-text-secondary);
}

.form-card :deep(.van-field__body),
.form-card :deep(.van-field__control) {
  display: flex;
  min-height: 28px;
  align-items: center;
}

.form-card :deep(.van-field__control) {
  line-height: var(--line-normal);
}

.form-card :deep(textarea) {
  min-height: 76px;
  align-items: flex-start;
  line-height: var(--line-relaxed);
}

.photo-field {
  display: grid;
  grid-template-columns: 70px minmax(0, 1fr);
  gap: var(--space-md);
  min-height: 112px;
  align-items: center;
  padding: 14px var(--space-md);
}

.photo-field__label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-md);
  line-height: var(--line-normal);
}

.photo-field__body {
  min-width: 0;
}

.photo-field :deep(.van-uploader__upload),
.photo-field :deep(.van-uploader__preview-image) {
  width: 88px;
  height: 88px;
  border-radius: var(--radius-sm);
}

.photo-field :deep(.van-uploader__upload) {
  border: 1px dashed var(--color-border-strong);
  background: var(--color-surface-muted);
}

.photo-field :deep(.van-uploader__upload-text) {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.photo-field :deep(.van-image__img) {
  object-fit: cover;
}

.form-save-bar {
  position: sticky;
  bottom: 0;
  z-index: 4;
  margin: var(--space-sm) calc(var(--space-md) * -1) 0;
  padding: var(--space-md) var(--space-md) calc(var(--space-md) + var(--safe-bottom));
  background: linear-gradient(180deg, rgba(245, 245, 247, 0), var(--color-bg) 28%);
}

.form-save-bar :deep(.van-button) {
  min-height: 52px;
  box-shadow: var(--shadow-card);
}

@media (max-width: 340px) {
  .form-card--grid {
    grid-template-columns: 1fr;
  }

  .form-card--grid :deep(.van-cell:first-child) {
    border-right: 0;
  }
}
</style>
