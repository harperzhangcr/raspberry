<template>
  <article class="recycle-card">
    <div class="recycle-card__main" :class="{ 'recycle-card__main--with-photo': displayImageUrl }">
      <div v-if="displayImageUrl" class="recycle-card__photo">
        <img :src="displayImageUrl" :alt="medicine.name" loading="lazy" />
      </div>
      <div class="recycle-card__content">
        <div class="recycle-card__top">
          <div class="recycle-card__title">
            <h3>{{ medicine.name }}</h3>
            <p>{{ medicine.category }}</p>
          </div>
          <div class="recycle-card__stock" aria-label="删除前库存">
            <strong>{{ medicine.quantity }}</strong>
            <span>{{ medicine.unit }}</span>
          </div>
        </div>

        <p v-if="medicine.location" class="recycle-card__line">
          <van-icon name="location-o" />
          <span>位置：{{ medicine.location }}</span>
        </p>
        <p class="recycle-card__line">
          <van-icon name="clock-o" />
          <span>删除时间：{{ deletedTimeText }}</span>
        </p>
      </div>
    </div>

    <div class="recycle-card__actions">
      <van-button type="primary" size="small" @click="$emit('restore', medicine)">恢复</van-button>
      <van-button class="recycle-card__danger" size="small" plain @click="$emit('permanentDelete', medicine)">
        永久删除
      </van-button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { Medicine } from '../types';
import { resolveMedicineImageUrl } from '../services/medicineStorage';
import { formatDateTime } from '../utils/medicine';

const props = defineProps<{
  medicine: Medicine;
}>();

defineEmits<{
  restore: [medicine: Medicine];
  permanentDelete: [medicine: Medicine];
}>();

const displayImageUrl = ref('');
const deletedTimeText = computed(() =>
  props.medicine.deletedAt ? formatDateTime(props.medicine.deletedAt) : '未知',
);
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
.recycle-card {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-card-solid);
  box-shadow: var(--shadow-card);
}

.recycle-card__main {
  display: grid;
  gap: var(--space-md);
}

.recycle-card__main--with-photo {
  grid-template-columns: 72px minmax(0, 1fr);
  align-items: start;
}

.recycle-card__photo {
  width: 72px;
  overflow: hidden;
  aspect-ratio: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-muted);
}

.recycle-card__photo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recycle-card__content {
  min-width: 0;
}

.recycle-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
}

.recycle-card__title {
  min-width: 0;
}

.recycle-card__title h3 {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--color-text);
  font-size: var(--font-size-md);
  font-weight: 750;
  line-height: var(--line-normal);
}

.recycle-card__title p,
.recycle-card__line {
  margin: var(--space-xs) 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-relaxed);
}

.recycle-card__line {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: var(--space-xs);
}

.recycle-card__line span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.recycle-card__stock {
  display: inline-flex;
  min-width: 56px;
  min-height: 48px;
  flex: 0 0 auto;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.recycle-card__stock strong {
  color: var(--color-primary);
  font-size: 24px;
  line-height: 1;
}

.recycle-card__stock span {
  margin-top: var(--space-2xs);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.recycle-card__actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.recycle-card__danger {
  color: #b42318;
  border-color: rgba(180, 35, 24, 0.2);
  background: rgba(180, 35, 24, 0.06);
}

@media (max-width: 340px) {
  .recycle-card__main--with-photo {
    grid-template-columns: 64px minmax(0, 1fr);
  }

  .recycle-card__photo {
    width: 64px;
  }
}
</style>
