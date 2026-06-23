<template>
  <article class="medicine-card" @click="$emit('detail', medicine)">
    <div class="medicine-card__main" :class="{ 'medicine-card__main--with-photo': displayImageUrl }">
      <div v-if="displayImageUrl" class="medicine-card__photo">
        <img :src="displayImageUrl" :alt="medicine.name" loading="lazy" />
      </div>
      <div class="medicine-card__content">
        <div class="medicine-card__top">
          <div class="medicine-card__title">
            <h3>{{ medicine.name }}</h3>
            <p>{{ medicine.category }} · 有效期 {{ medicine.expiryDate }}</p>
          </div>
          <div class="medicine-card__stock" aria-label="当前库存">
            <strong>{{ medicine.quantity }}</strong>
            <span>{{ medicine.unit }}</span>
          </div>
        </div>

        <p v-if="medicine.location" class="medicine-card__location">
          <van-icon name="location-o" />
          <span>位置：{{ medicine.location }}</span>
        </p>
      </div>
    </div>

    <div class="medicine-card__tags">
      <van-tag v-for="label in status.labels" :key="label.text" :type="label.type">
        {{ label.text }}
      </van-tag>
    </div>

    <p v-if="medicine.note" class="medicine-card__note">{{ medicine.note }}</p>

    <button v-if="medicine.batches.length > 0" class="medicine-card__batch-toggle" type="button" @click.stop="showBatches = !showBatches">
      <span>库存明细</span>
      <span>{{ medicine.batches.length }} 批</span>
      <van-icon name="arrow-down" :class="{ 'medicine-card__batch-icon--open': showBatches }" />
    </button>

    <div v-if="showBatches && medicine.batches.length > 0" class="medicine-card__batches" @click.stop>
      <div v-for="batch in sortedBatches" :key="batch.id" class="medicine-card__batch-row">
        <span>有效期 {{ batch.expiryDate }}</span>
        <strong>{{ batch.quantity }}{{ medicine.unit }}</strong>
      </div>
    </div>

    <div class="medicine-card__actions" @click.stop>
      <div class="medicine-card__quantity-actions">
        <van-button
          icon="minus"
          size="small"
          :disabled="medicine.quantity === 0"
          aria-label="库存减一"
          @click="$emit('adjust', medicine, -1)"
        />
        <van-button icon="plus" size="small" type="primary" aria-label="新增库存批次" @click="$emit('addBatch', medicine)" />
      </div>
      <div class="medicine-card__manage-actions">
        <van-button icon="edit" size="small" plain aria-label="编辑药品" @click="$emit('edit', medicine)" />
        <van-button icon="delete-o" size="small" plain aria-label="删除药品" @click="$emit('delete', medicine)" />
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { Medicine } from '../types';
import { resolveMedicineImageUrl } from '../services/medicineStorage';
import { getMedicineStatus, sortBatches } from '../utils/medicine';

const props = defineProps<{
  medicine: Medicine;
}>();

defineEmits<{
  detail: [medicine: Medicine];
  edit: [medicine: Medicine];
  delete: [medicine: Medicine];
  adjust: [medicine: Medicine, delta: -1];
  addBatch: [medicine: Medicine];
}>();

const showBatches = ref(false);
const displayImageUrl = ref('');
const status = computed(() => getMedicineStatus(props.medicine));
const sortedBatches = computed(() => sortBatches(props.medicine.batches));
let imageRequestId = 0;

watch(
  () => props.medicine.imageUrl,
  async (imageUrl) => {
    const requestId = ++imageRequestId;
    displayImageUrl.value = '';
    const resolved = await resolveMedicineImageUrl(imageUrl);
    if (requestId === imageRequestId) {
      displayImageUrl.value = resolved;
    }
  },
  { immediate: true },
);
</script>

<style scoped>
.medicine-card {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-card-solid);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition:
    transform var(--duration-fast) ease,
    box-shadow var(--duration-normal) ease,
    border-color var(--duration-normal) ease;
}

.medicine-card:active {
  transform: scale(0.985);
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-card-hover);
}

.medicine-card__main {
  display: grid;
  gap: var(--space-md);
}

.medicine-card__main--with-photo {
  grid-template-columns: 88px minmax(0, 1fr);
  align-items: start;
}

.medicine-card__photo {
  width: 88px;
  overflow: hidden;
  aspect-ratio: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-muted);
}

.medicine-card__photo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.medicine-card__content {
  min-width: 0;
}

.medicine-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
}

.medicine-card__title {
  min-width: 0;
}

.medicine-card__title h3 {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--color-text);
  font-size: var(--font-size-lg);
  font-weight: 750;
  line-height: var(--line-normal);
}

.medicine-card__title p,
.medicine-card__note,
.medicine-card__location {
  margin: var(--space-xs) 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-relaxed);
}

.medicine-card__location {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: var(--space-xs);
}

.medicine-card__location span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.medicine-card__stock {
  display: inline-flex;
  min-width: 68px;
  min-height: 56px;
  flex: 0 0 auto;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.medicine-card__stock strong {
  color: var(--color-primary);
  font-size: 28px;
  line-height: 1;
}

.medicine-card__stock span {
  margin-top: var(--space-2xs);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.medicine-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.medicine-card__note {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.medicine-card__batch-toggle {
  display: grid;
  width: 100%;
  min-height: 38px;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  padding: 0 var(--space-sm);
  border: 1px solid rgba(255, 159, 10, 0.18);
  border-radius: var(--radius-md);
  color: #9a5a00;
  background: var(--color-warning-soft);
  font-size: var(--font-size-sm);
  font-weight: 500;
  line-height: var(--line-relaxed);
  text-align: left;
}

.medicine-card__batch-icon--open {
  transform: rotate(180deg);
}

.medicine-card__batches {
  display: grid;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.medicine-card__batch-row {
  display: flex;
  min-height: 38px;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: 0 var(--space-sm);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  background: var(--color-bg);
  font-size: var(--font-size-sm);
  font-weight: 500;
  line-height: var(--line-relaxed);
}

.medicine-card__batch-row strong {
  color: var(--color-text);
  font-weight: 700;
}

.medicine-card__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.medicine-card__quantity-actions,
.medicine-card__manage-actions {
  display: flex;
  gap: var(--space-sm);
}

.medicine-card__actions :deep(.van-button) {
  width: var(--tap-size);
  min-width: var(--tap-size);
  padding: 0;
  border-radius: var(--radius-pill);
}

.medicine-card__manage-actions :deep(.van-button) {
  color: var(--color-text-secondary);
  border-color: var(--color-border);
  background: var(--color-surface-muted);
}

@media (max-width: 340px) {
  .medicine-card {
    padding: 14px;
  }

  .medicine-card__stock {
    min-width: 60px;
  }

  .medicine-card__main--with-photo {
    grid-template-columns: 72px minmax(0, 1fr);
  }

  .medicine-card__photo {
    width: 72px;
  }
}
</style>
