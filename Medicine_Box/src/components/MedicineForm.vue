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
      <div class="form-scroll">
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
            placeholder="请选择分类，可由AI识别填入"
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
            v-model="form.dosageTiming"
            is-link
            readonly
            name="dosageTiming"
            label="服用方法"
            placeholder="请选择服用方法"
            :rules="[{ required: true, message: '请选择服用方法' }]"
            @click="showDosageTimingPicker = true"
          />
          <div class="dosage-cycle-field">
            <div class="dosage-cycle-field__label">用药周期</div>
            <div class="dosage-cycle-field__controls">
              <div class="dosage-cycle-part">
                <span>一日</span>
                <button type="button" class="dosage-cycle-select" @click="openDosageCyclePicker('frequency')">
                  {{ dosageCycleParts.frequency }}
                </button>
                <span>次</span>
              </div>
              <div class="dosage-cycle-part">
                <span>每次</span>
                <button type="button" class="dosage-cycle-select" @click="openDosageCyclePicker('dose')">
                  {{ dosageCycleParts.dose }}
                </button>
                <span>颗</span>
              </div>
              <div class="dosage-cycle-part dosage-cycle-part--duration">
                <span>连续</span>
                <button type="button" class="dosage-cycle-select" @click="openDosageCyclePicker('duration')">
                  {{ dosageCycleParts.duration }}
                </button>
                <button type="button" class="dosage-cycle-select" @click="openDosageCyclePicker('durationUnit')">
                  {{ dosageCycleParts.durationUnit }}
                </button>
              </div>
            </div>
          </div>
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
              <div v-if="form.imageUrl" class="ai-recognition">
                <div v-if="isRecognizing" class="ai-recognition__status">
                  <van-loading size="14" color="var(--color-primary)" />
                  <span>正在识别药品信息...</span>
                </div>
                <p v-else-if="recognizeError" class="ai-recognition__error">{{ recognizeError }}</p>
                <van-button
                  class="ai-recognition__retry"
                  size="mini"
                  plain
                  type="primary"
                  :disabled="isRecognizing"
                  @click="retryRecognizeImage"
                >
                  {{ isRecognizing ? '识别中...' : '重新识别' }}
                </van-button>
              </div>
            </div>
          </div>
        </section>
      </div>

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
    <van-popup v-model:show="showDosageTimingPicker" position="bottom" round>
      <van-picker
        title="选择服用方法"
        :columns="dosageTimingColumns"
        @confirm="onDosageTimingConfirm"
        @cancel="showDosageTimingPicker = false"
      />
    </van-popup>
    <van-popup v-model:show="showDosageCyclePicker" position="bottom" round>
      <van-picker
        :title="dosageCyclePickerTitle"
        :columns="dosageCyclePickerColumns"
        @confirm="onDosageCycleConfirm"
        @cancel="showDosageCyclePicker = false"
      />
    </van-popup>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { showFailToast, showSuccessToast, showToast } from 'vant';
import type { UploaderFileListItem } from 'vant';
import type { AiMedicineRecognition, Medicine, MedicineInput } from '../types';
import {
  isCloudFileId,
  isLikelyHeicImage,
  resolveTempImageUrl,
  uploadMedicineImage,
} from '../services/medicineStorage';
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
const showDosageTimingPicker = ref(false);
const showDosageCyclePicker = ref(false);
const imageFileList = ref<UploaderFileListItem[]>([]);
const matchedMedicine = ref<Medicine | null>(null);
const isRecognizing = ref(false);
const recognizeError = ref<string | null>(null);
const lastRecognizedImageUrl = ref<string | null>(null);
const recognizeTimeoutMs = 15000;
const form = reactive<MedicineInput>({
  name: '',
  category: '',
  quantity: 1,
  unit: '盒',
  expiryDate: todayDateString(),
  note: '',
  location: '',
  imageUrl: '',
  dosageTiming: '不限',
  dosageCycle: '',
});
type DosageCyclePart = 'frequency' | 'dose' | 'duration' | 'durationUnit';

const dosageCycleParts = reactive<Record<DosageCyclePart, string>>({
  frequency: '',
  dose: '',
  duration: '',
  durationUnit: '天',
});
const activeDosageCyclePart = ref<DosageCyclePart>('frequency');

const categoryColumns = computed(() => props.categories.map((category) => ({ text: category, value: category })));
const dosageTimingColumns = ['不限', '饭前', '饭后'].map((value) => ({ text: value, value }));
const emptyPickerOption = { text: '不填', value: '' };
const dosageFrequencyColumns = [
  emptyPickerOption,
  ...Array.from({ length: 6 }, (_, index) => {
    const value = String(index + 1);
    return { text: value, value };
  }),
];
const dosageDoseColumns = [
  emptyPickerOption,
  ...Array.from({ length: 6 }, (_, index) => {
    const value = String(index + 1);
    return { text: value, value };
  }),
];
const dosageDurationColumns = [
  emptyPickerOption,
  ...Array.from({ length: 30 }, (_, index) => {
    const value = String(index + 1);
    return { text: value, value };
  }),
];
const dosageDurationUnitColumns = ['天', '周', '月'].map((text) => ({
  text,
  value: text,
}));
const dosageCyclePickerTitle = computed(() => {
  const titles: Record<DosageCyclePart, string> = {
    frequency: '选择每日次数',
    dose: '选择每次数量',
    duration: '选择连续服药时长',
    durationUnit: '选择时长单位',
  };
  return titles[activeDosageCyclePart.value];
});
const dosageCyclePickerColumns = computed(() => {
  const columns: Record<DosageCyclePart, Array<{ text: string; value: string }>> = {
    frequency: dosageFrequencyColumns,
    dose: dosageDoseColumns,
    duration: dosageDurationColumns,
    durationUnit: dosageDurationUnitColumns,
  };
  return columns[activeDosageCyclePart.value];
});
const isNameLocked = computed(() => !props.medicine && !!matchedMedicine.value);
let imagePreviewRequestId = 0;
let nameLookupRequestId = 0;
let nameLookupTimer: number | undefined;
let aiRecognitionRequestId = 0;
const AI_RECOGNITION_FAIL_MESSAGE = 'AI识别失败，可手动填写';
const AI_RECOGNITION_TIMEOUT_MESSAGE = 'AI识别时间较长，请手动填写或稍后重试';

function setUploaderPreview(previewUrl: string) {
  imageFileList.value = [
    {
      url: previewUrl,
      isImage: true,
      status: 'done',
    },
  ];
}

function buildDosageCycle() {
  const parts: string[] = [];
  if (dosageCycleParts.frequency) {
    parts.push(`一日${dosageCycleParts.frequency}次`);
  }
  if (dosageCycleParts.dose) {
    parts.push(`每次${dosageCycleParts.dose}颗`);
  }
  if (dosageCycleParts.duration) {
    parts.push(`需连续服药${dosageCycleParts.duration}${dosageCycleParts.durationUnit}`);
  }
  form.dosageCycle = parts.join('；');
}

function syncDosageCycleParts(value?: string) {
  const text = String(value || '').trim();
  const frequencyMatch = text.match(/一日([^；;,，\s]+)次/);
  const doseMatch = text.match(/每次([^；;,，\s]+)颗/);
  const durationMatch = text.match(/(?:需)?连续服药(\d+)(天|周|月)?/);

  dosageCycleParts.frequency = frequencyMatch?.[1] || '';
  dosageCycleParts.dose = doseMatch?.[1] || '';
  dosageCycleParts.duration = durationMatch?.[1] || '';
  dosageCycleParts.durationUnit = durationMatch?.[2] || '天';
  buildDosageCycle();
}

async function syncImagePreview(imageUrl?: string) {
  const requestId = ++imagePreviewRequestId;
  const value = String(imageUrl || '').trim();
  if (!value) {
    imageFileList.value = [];
    return;
  }
  const previewUrl = await resolveTempImageUrl(value);
  if (requestId !== imagePreviewRequestId) return;
  if (!previewUrl) {
    imageFileList.value = [];
    return;
  }
  setUploaderPreview(previewUrl);
}

watch(
  () => props.medicine,
  (medicine) => {
    matchedMedicine.value = null;
    form.name = medicine?.name || '';
    form.category = medicine?.category || '';
    form.quantity = medicine ? medicine.quantity : 1;
    form.unit = medicine?.unit || '盒';
    form.expiryDate = medicine?.expiryDate || todayDateString();
    form.note = medicine?.note || '';
    form.location = medicine?.location || '';
    form.imageUrl = normalizePersistedImageUrl(medicine?.imageUrl);
    form.dosageTiming = medicine?.dosageTiming || '不限';
    form.dosageCycle = medicine?.dosageCycle || '';
    syncDosageCycleParts(medicine?.dosageCycle);
    isRecognizing.value = false;
    recognizeError.value = null;
    lastRecognizedImageUrl.value = null;
    aiRecognitionRequestId += 1;
    void syncImagePreview(form.imageUrl);
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
    form.imageUrl = normalizePersistedImageUrl(form.imageUrl) || normalizePersistedImageUrl(existing.imageUrl);
    form.dosageTiming = existing.dosageTiming || '不限';
    form.dosageCycle = existing.dosageCycle || '';
    syncDosageCycleParts(existing.dosageCycle);
    void syncImagePreview(form.imageUrl);
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

function isEmptyField(value?: string) {
  return !String(value || '').trim();
}

function getImagePrefix(value?: string) {
  return String(value || '').trim().slice(0, 80);
}

function applyRecognitionResult(result: AiMedicineRecognition) {
  if (props.medicine || matchedMedicine.value) return;
  console.log('[MedicineForm] before AI backfill form.imageUrl:', getImagePrefix(form.imageUrl));
  if (isEmptyField(form.name) && result.name.trim()) {
    form.name = result.name.trim();
  }
  const category = normalizeRecognizedCategory(result.category);
  if (isEmptyField(form.category) && category) {
    form.category = category;
  }
  if (isEmptyField(form.note) && result.indications.trim()) {
    form.note = result.indications.trim();
  }
  console.log('[MedicineForm] after AI backfill form.imageUrl:', getImagePrefix(form.imageUrl));
}

function withRecognitionTimeout<T>(promise: Promise<T>) {
  let timeoutId: number | undefined;
  const timeoutPromise = new Promise<T>((_, reject) => {
    timeoutId = window.setTimeout(() => {
      reject(new Error(AI_RECOGNITION_TIMEOUT_MESSAGE));
    }, recognizeTimeoutMs);
  });

  return Promise.race([promise, timeoutPromise]).finally(() => {
    if (timeoutId) {
      window.clearTimeout(timeoutId);
    }
  });
}

function isRecognitionTimeout(error: unknown) {
  return error instanceof Error && error.message === AI_RECOGNITION_TIMEOUT_MESSAGE;
}

function isDataUrl(value: string) {
  return value.startsWith('data:');
}

function normalizePersistedImageUrl(imageUrl?: string) {
  const value = String(imageUrl || '').trim();
  return isCloudFileId(value) ? value : '';
}

async function recognizeUploadedImage(imageUrl: string) {
  const value = String(imageUrl || '').trim();
  if (!value || !props.recognizeMedicineImage) return;
  if (isDataUrl(value)) {
    console.error('[MedicineForm] AI recognition blocked: data URL cannot be used as imageUrl');
    recognizeError.value = '图片未上传到云端，请重新选择';
    showFailToast('图片未上传到云端，请重新选择');
    return;
  }
  console.log('[MedicineForm] start AI recognition:', { imageUrl: value });
  const requestId = ++aiRecognitionRequestId;
  isRecognizing.value = true;
  recognizeError.value = null;

  try {
    const result = await withRecognitionTimeout(props.recognizeMedicineImage(value));
    console.log('[MedicineForm] AI recognition result:', result);
    if (requestId !== aiRecognitionRequestId) return;
    applyRecognitionResult(result);
    lastRecognizedImageUrl.value = value;
    showSuccessToast('已识别并填入药品信息');
  } catch (error) {
    console.error('[MedicineForm] AI recognition failed:', error);
    if (requestId === aiRecognitionRequestId) {
      const message = isRecognitionTimeout(error) ? AI_RECOGNITION_TIMEOUT_MESSAGE : AI_RECOGNITION_FAIL_MESSAGE;
      recognizeError.value = message;
      showFailToast(message);
    }
  } finally {
    if (requestId === aiRecognitionRequestId) {
      isRecognizing.value = false;
    }
  }
}

function retryRecognizeImage() {
  void recognizeUploadedImage(form.imageUrl || '');
}

function onCategoryConfirm(event: { selectedOptions: Array<{ text: string; value: string }> }) {
  form.category = event.selectedOptions[0]?.value || '';
  showCategoryPicker.value = false;
}

function onDosageTimingConfirm(event: { selectedOptions: Array<{ text: string; value: string }> }) {
  form.dosageTiming = event.selectedOptions[0]?.value || '不限';
  showDosageTimingPicker.value = false;
}

function openDosageCyclePicker(part: DosageCyclePart) {
  activeDosageCyclePart.value = part;
  showDosageCyclePicker.value = true;
}

function onDosageCycleConfirm(event: { selectedOptions: Array<{ text: string; value: string }> }) {
  dosageCycleParts[activeDosageCyclePart.value] = event.selectedOptions[0]?.value || '';
  buildDosageCycle();
  showDosageCyclePicker.value = false;
}

async function handleImageRead(item: UploaderFileListItem | UploaderFileListItem[]) {
  const fileItem = Array.isArray(item) ? item[0] : item;
  if (!fileItem?.file) return;

  if (isLikelyHeicImage(fileItem.file)) {
    showToast('当前图片格式可能不兼容，请使用 JPG/PNG 图片');
  }

  fileItem.status = 'uploading';
  fileItem.message = '上传中';

  try {
    const fileID = await uploadMedicineImage(fileItem.file);
    if (!isCloudFileId(fileID)) {
      console.warn('[MedicineForm] upload did not return CloudBase fileID, skip save and AI recognition:', {
        prefix: fileID.slice(0, 32),
      });
      form.imageUrl = '';
      const localPreviewUrl = fileItem.objectUrl || fileItem.content || fileID;
      if (localPreviewUrl) {
        setUploaderPreview(localPreviewUrl);
      } else {
        imageFileList.value = [];
      }
      showFailToast('当前未上传到云端，图片不会用于 AI 识别');
      return;
    }

    console.log('[MedicineForm] uploaded fileID:', fileID);
    form.imageUrl = fileID;
    const previewUrl = await resolveTempImageUrl(fileID);
    if (previewUrl) {
      setUploaderPreview(previewUrl);
    } else {
      imageFileList.value = [];
      showFailToast('图片已上传，预览暂不可用');
    }
    void recognizeUploadedImage(fileID);
  } catch {
    fileItem.status = 'failed';
    fileItem.message = '上传失败';
    const message = isLikelyHeicImage(fileItem.file)
      ? '当前图片格式可能不兼容，请使用 JPG/PNG 图片'
      : '图片上传失败，仍可保存药品信息';
    showFailToast(message);
  }
}

function handleImageDelete() {
  aiRecognitionRequestId += 1;
  isRecognizing.value = false;
  recognizeError.value = null;
  lastRecognizedImageUrl.value = null;
  form.imageUrl = '';
  imageFileList.value = [];
  return true;
}

function submit() {
  buildDosageCycle();
  const payloadImageUrl = normalizePersistedImageUrl(form.imageUrl);
  console.log('[MedicineForm] submit payload.imageUrl:', getImagePrefix(payloadImageUrl));
  emit('submit', {
    name: form.name.trim(),
    category: form.category,
    quantity: Math.max(0, Number(form.quantity) || 0),
    unit: form.unit.trim(),
    expiryDate: form.expiryDate,
    note: form.note?.trim(),
    location: form.location?.trim(),
    imageUrl: payloadImageUrl,
    dosageTiming: form.dosageTiming?.trim() || '不限',
    dosageCycle: form.dosageCycle?.trim(),
  }, matchedMedicine.value);
}
</script>

<style scoped>
.form-panel {
  display: flex;
  flex-direction: column;
  height: min(88vh, 760px);
  min-height: min(74vh, 680px);
  box-sizing: border-box;
  overflow: hidden;
  padding: var(--space-lg) var(--space-md) 0;
  background: var(--color-bg);
}

.form-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex: 0 0 auto;
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
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-height: 0;
}

.form-scroll {
  display: grid;
  flex: 1 1 auto;
  gap: var(--space-md);
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-bottom: var(--space-md);
  -webkit-overflow-scrolling: touch;
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

.dosage-cycle-field {
  display: grid;
  grid-template-columns: 70px minmax(0, 1fr);
  gap: var(--space-md);
  align-items: center;
  min-height: 72px;
  padding: 14px var(--space-md);
}

.dosage-cycle-field__label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-md);
  line-height: var(--line-normal);
}

.dosage-cycle-field__controls {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  min-width: 0;
}

.dosage-cycle-part {
  display: inline-flex;
  flex: 0 1 auto;
  gap: 4px;
  align-items: center;
  color: var(--color-text);
  font-size: var(--font-size-sm);
  line-height: var(--line-normal);
  white-space: nowrap;
}

.dosage-cycle-part--duration {
  flex-wrap: wrap;
}

.dosage-cycle-select {
  min-width: 48px;
  height: 30px;
  padding: 0 var(--space-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-muted);
  color: var(--color-primary);
  font: inherit;
  line-height: 28px;
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

.ai-recognition {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs) var(--space-sm);
  align-items: center;
  margin-top: var(--space-sm);
}

.ai-recognition__status {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  line-height: var(--line-normal);
}

.ai-recognition__error {
  flex-basis: 100%;
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-xs);
  line-height: var(--line-relaxed);
}

.ai-recognition__retry {
  min-height: 28px;
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
  flex: 0 0 auto;
  z-index: 4;
  margin: 0 calc(var(--space-md) * -1);
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
