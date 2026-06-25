<template>
  <section class="health-check-panel">
    <div class="health-check__header">
      <div>
        <p class="eyebrow">Medicine Check</p>
        <h2>药箱体检</h2>
        <p class="health-check__subtitle">已为你检查家庭药箱库存状态</p>
      </div>
      <van-button class="icon-close-button" icon="cross" size="small" plain aria-label="关闭药箱体检" @click="$emit('close')" />
    </div>

    <template v-if="activeView === 'overview'">
      <section class="health-section">
        <h3>需要处理</h3>
        <div class="health-grid">
          <button
            v-for="item in actionStats"
            :key="item.key"
            class="health-card"
            type="button"
            @click="openView(item.key)"
          >
            <div>
              <span>{{ item.title }}</span>
              <strong>{{ item.count }}</strong>
            </div>
            <p>{{ item.description }}</p>
            <em>{{ item.action }}</em>
          </button>
        </div>
      </section>

      <section class="health-section">
        <h3>状态良好</h3>
        <button class="health-card health-card--good" type="button" @click="openView('normal')">
          <div>
            <span>有正常效期库存</span>
            <strong>{{ normalMedicines.length }}</strong>
          </div>
          <p>状态良好</p>
          <em>查看</em>
        </button>
      </section>
    </template>

    <template v-else>
      <div class="health-view-title">
        <van-button class="text-back-button" icon="arrow-left" size="small" plain @click="backToOverview">返回</van-button>
        <div>
          <h3>{{ currentViewConfig.title }}</h3>
          <p>{{ currentViewConfig.description }}</p>
        </div>
      </div>

      <van-empty v-if="currentMedicines.length === 0" description="暂无药品" />

      <template v-else-if="activeView === 'expired'">
        <van-checkbox-group v-model="selectedExpiredIds" class="health-list">
          <van-checkbox
            v-for="medicine in expiredMedicines"
            :key="medicine._id"
            :name="medicine._id"
            shape="square"
          >
            <div class="health-list-item">
              <strong>{{ medicine.name }}</strong>
              <span>{{ medicine.category }} · {{ medicine.quantity }}{{ medicine.unit }} · {{ medicine.expiryDate }}</span>
            </div>
          </van-checkbox>
        </van-checkbox-group>

        <div class="health-batch-bar">
          <span>已选 {{ selectedExpiredIds.length }} 个</span>
          <van-button
            type="danger"
            size="small"
            :disabled="selectedExpiredIds.length === 0"
            @click="$emit('move-expired-to-recycle', selectedExpiredIds)"
          >
            移入回收站
          </van-button>
        </div>
      </template>

      <section v-else class="health-list">
        <article v-for="medicine in currentMedicines" :key="medicine._id" class="health-list-item">
          <strong>{{ medicine.name }}</strong>
          <span>{{ medicine.category }} · {{ medicine.quantity }}{{ medicine.unit }} · {{ medicine.expiryDate }}</span>
        </article>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { Medicine } from '../types';
import { getMedicineStatus, sortMedicines } from '../utils/medicine';

type HealthView = 'overview' | 'expired' | 'expiringSoon' | 'outOfStock' | 'normal';

const props = defineProps<{
  medicines: Medicine[];
}>();

defineEmits<{
  close: [];
  'move-expired-to-recycle': [ids: string[]];
}>();

const activeView = ref<HealthView>('overview');
const selectedExpiredIds = ref<string[]>([]);

const sortedMedicines = computed(() => sortMedicines(props.medicines));
const expiredMedicines = computed(() =>
  sortedMedicines.value.filter((medicine) => getMedicineStatus(medicine).expiryStatus === 'expired'),
);
const expiringSoonMedicines = computed(() =>
  sortedMedicines.value.filter((medicine) => {
    const status = getMedicineStatus(medicine);
    return status.expiryStatus === 'expiringSoon' && !status.isOutOfStock;
  }),
);
const outOfStockMedicines = computed(() =>
  sortedMedicines.value.filter((medicine) => getMedicineStatus(medicine).isOutOfStock),
);
const normalMedicines = computed(() =>
  sortedMedicines.value.filter((medicine) => {
    const status = getMedicineStatus(medicine);
    return !status.isOutOfStock && status.expiryStatus !== 'expired';
  }),
);

const actionStats = computed(() => [
  {
    key: 'expired' as const,
    title: '已过期',
    count: expiredMedicines.value.length,
    description: '建议清理',
    action: '查看并清理',
  },
  {
    key: 'expiringSoon' as const,
    title: '30天内过期',
    count: expiringSoonMedicines.value.length,
    description: '建议优先使用',
    action: '查看临期药',
  },
  {
    key: 'outOfStock' as const,
    title: '缺货',
    count: outOfStockMedicines.value.length,
    description: '可补货',
    action: '查看缺货药',
  },
]);

const viewConfigs = {
  expired: { title: '已过期', description: '建议清理，移入回收站后仍可恢复' },
  expiringSoon: { title: '30天内过期', description: '建议优先使用' },
  outOfStock: { title: '缺货', description: '可补货' },
  normal: { title: '有正常效期库存', description: '状态良好' },
};

const currentViewConfig = computed(() => {
  if (activeView.value === 'overview') return { title: '', description: '' };
  return viewConfigs[activeView.value];
});

const currentMedicines = computed(() => {
  if (activeView.value === 'expired') return expiredMedicines.value;
  if (activeView.value === 'expiringSoon') return expiringSoonMedicines.value;
  if (activeView.value === 'outOfStock') return outOfStockMedicines.value;
  if (activeView.value === 'normal') return normalMedicines.value;
  return [];
});

function openView(view: Exclude<HealthView, 'overview'>) {
  activeView.value = view;
  if (view === 'expired') {
    selectedExpiredIds.value = expiredMedicines.value.map((medicine) => medicine._id);
  }
}

function backToOverview() {
  activeView.value = 'overview';
}

watch(
  expiredMedicines,
  (items) => {
    if (activeView.value !== 'expired') return;
    const ids = new Set(items.map((medicine) => medicine._id));
    selectedExpiredIds.value = selectedExpiredIds.value.filter((id) => ids.has(id));
  },
  { deep: true },
);
</script>

<style scoped>
.health-check-panel {
  display: flex;
  flex-direction: column;
  height: min(88vh, 760px);
  max-height: min(88vh, 760px);
  padding: var(--space-lg) var(--space-md) calc(var(--space-lg) + var(--safe-bottom));
  overflow: hidden;
  background: var(--color-bg);
}

.health-check__header {
  display: flex;
  flex: 0 0 auto;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.health-check__header h2,
.health-section h3,
.health-view-title h3 {
  margin: 0;
  color: var(--color-text);
  line-height: var(--line-tight);
}

.health-check__header h2 {
  font-size: var(--font-size-xl);
}

.health-check__subtitle,
.health-view-title p,
.health-card p,
.health-list-item span {
  margin: var(--space-xs) 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-relaxed);
}

.health-check__header .eyebrow {
  margin: 0 0 var(--space-sm);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 700;
  line-height: var(--line-normal);
}

.health-check__subtitle {
  margin-top: var(--space-sm);
  font-size: var(--font-size-md);
}

.health-section {
  display: grid;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.health-section h3,
.health-view-title h3 {
  font-size: var(--font-size-lg);
}

.health-grid {
  display: grid;
  gap: var(--space-sm);
}

.health-card {
  display: grid;
  gap: var(--space-xs);
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-card-solid);
  box-shadow: var(--shadow-card);
  color: inherit;
  text-align: left;
}

.health-card div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.health-card span {
  font-size: var(--font-size-md);
  font-weight: 700;
}

.health-card strong {
  color: var(--color-primary);
  font-size: var(--font-size-xl);
  line-height: var(--line-tight);
}

.health-card em {
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-style: normal;
  font-weight: 700;
}

.health-card--good {
  background: linear-gradient(180deg, var(--color-card-solid), var(--color-primary-soft));
}

.health-view-title {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--space-md);
  align-items: center;
  margin-bottom: var(--space-md);
}

.text-back-button {
  width: auto;
  min-width: 0;
  min-height: var(--tap-size);
  padding: 0;
  border: 0;
  border-radius: 0;
  color: var(--color-text-secondary);
  background: transparent;
  box-shadow: none;
}

.text-back-button::before {
  display: none;
}

.text-back-button :deep(.van-button__content) {
  gap: 2px;
}

.text-back-button :deep(.van-button__icon) {
  margin: 0;
  font-size: 18px;
}

.health-list {
  display: grid;
  gap: var(--space-sm);
  min-height: 0;
  overflow-y: auto;
  padding-bottom: var(--space-md);
  -webkit-overflow-scrolling: touch;
}

.health-list-item {
  display: grid;
  min-width: 0;
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-card-solid);
}

.health-list :deep(.van-checkbox) {
  align-items: stretch;
}

.health-list :deep(.van-checkbox__label) {
  flex: 1;
}

.health-batch-bar {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  margin: var(--space-sm) calc(var(--space-md) * -1) calc((var(--space-lg) + var(--safe-bottom)) * -1);
  padding: var(--space-md) var(--space-md) calc(var(--space-md) + var(--safe-bottom));
  background: linear-gradient(180deg, rgba(245, 245, 247, 0), var(--color-bg) 28%);
}

.health-batch-bar span {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
