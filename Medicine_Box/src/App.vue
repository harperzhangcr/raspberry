<template>
  <main class="app-shell">
    <section v-if="!familyCode" class="access-page">
      <div class="access-panel">
        <p class="eyebrow">Family Medicine Box</p>
        <h1>家庭药箱</h1>
        <p class="access-copy">输入家庭访问码后继续，下次打开会自动进入。</p>

        <div class="access-form">
          <van-field
            v-model="codeInput"
            type="password"
            label="访问码"
            placeholder="请输入家庭访问码"
            clearable
            @keyup.enter="handleVerifyCode"
          />
          <van-button type="primary" block :loading="loading" @click="handleVerifyCode">进入药箱</van-button>
        </div>
      </div>
    </section>

    <section v-else class="medicine-app">
      <header class="topbar">
        <div>
          <p class="eyebrow">Family Medicine Box</p>
          <h1>家庭药箱</h1>
          <p class="topbar-subtitle">快速找到家里的常用药</p>
        </div>
        <div class="topbar-actions">
          <van-popover
            v-model:show="showMoreMenu"
            placement="bottom-end"
            :actions="moreMenuActions"
            @select="handleMoreMenuSelect"
          >
            <template #reference>
              <button class="topbar-more-button" type="button" aria-label="更多菜单">⋯</button>
            </template>
          </van-popover>
        </div>
      </header>

      <div class="search-wrap">
        <van-search v-model="keyword" placeholder="搜索药品名称" shape="round" />
      </div>

      <van-tabs v-model:active="activeTab" class="tabs-shell">
        <van-tab title="分类药箱" name="home">
          <GlobalActionBar @add-medicine="openCreateForm" @open-health-check="showHealthCheck = true" />

          <section v-if="loading && medicines.length === 0" class="loading-panel">
            <van-loading color="var(--color-primary)">正在整理药箱</van-loading>
          </section>
          <van-empty v-else-if="categoryGroups.length === 0" description="暂无药品，先新增常用药" />
          <section v-else class="category-list">
            <article v-for="group in categoryGroups" :key="group.category" class="category-section">
              <button
                class="category-header"
                :class="{ 'category-header--visual': getCategoryAsset(group.category) }"
                type="button"
                @click="toggleCategory(group.category)"
              >
                <img
                  v-if="getCategoryAsset(group.category)"
                  class="category-banner"
                  :src="getCategoryAsset(group.category)"
                  alt=""
                  loading="lazy"
                />
                <div class="category-header-main">
                  <h2>{{ group.category }}</h2>
                  <div class="category-flags">
                    <van-tag v-if="group.hasOutOfStock" type="danger">有缺货</van-tag>
                    <van-tag v-if="group.hasExpired" type="danger" plain>有过期</van-tag>
                  </div>
                </div>
                <div class="category-meta">
                  <span class="category-count">{{ group.medicines.length }} 种</span>
                  <span class="category-toggle" :class="{ 'category-toggle--open': isCategoryExpanded(group.category) }">
                    <van-icon name="arrow-down" />
                  </span>
                </div>
              </button>

              <div v-if="isCategoryExpanded(group.category)" class="card-grid">
                <MedicineCard
                  v-for="medicine in group.medicines"
                  :key="medicine._id"
                  :medicine="medicine"
                  @detail="openDetail"
                  @edit="openEditForm"
                  @delete="handleDelete"
                  @adjust="handleAdjustQuantity"
                  @add-batch="openBatchForm"
                  @update-batch="handleUpdateBatch"
                  @delete-batch="handleDeleteBatch"
                />
              </div>
            </article>
          </section>
        </van-tab>

        <van-tab title="全部列表" name="list">
          <GlobalActionBar @add-medicine="openCreateForm" @open-health-check="showHealthCheck = true" />

          <section v-if="loading && medicines.length === 0" class="loading-panel">
            <van-loading color="var(--color-primary)">正在加载药品</van-loading>
          </section>
          <van-empty v-else-if="filteredMedicines.length === 0" description="没有匹配的药品" />
          <section v-else class="list-stack">
            <MedicineCard
              v-for="medicine in filteredMedicines"
              :key="medicine._id"
              :medicine="medicine"
              @detail="openDetail"
              @edit="openEditForm"
              @delete="handleDelete"
              @adjust="handleAdjustQuantity"
              @add-batch="openBatchForm"
              @update-batch="handleUpdateBatch"
              @delete-batch="handleDeleteBatch"
            />
          </section>
        </van-tab>
      </van-tabs>
    </section>

    <van-popup v-model:show="showForm" position="bottom" round class="sheet-popup">
      <MedicineForm
        :key="formKey"
        :medicine="editingMedicine"
        :categories="categories"
        :find-medicine-by-name="findMedicineForForm"
        :recognize-medicine-image="recognizeMedicineImageForForm"
        @cancel="showForm = false"
        @submit="handleSubmitMedicine"
      />
    </van-popup>

    <van-popup v-model:show="showBatchForm" position="bottom" round class="sheet-popup">
      <section v-if="batchMedicine" class="batch-panel">
        <div class="sheet-title">
          <div>
            <p class="eyebrow">Add Stock</p>
            <h2>新增库存</h2>
            <p>为当前药品补充新的库存批次</p>
          </div>
          <van-button class="icon-close-button" icon="cross" size="small" plain @click="showBatchForm = false" />
        </div>
        <div class="batch-target">
          <strong>{{ batchMedicine.name }}</strong>
          <span>当前 {{ batchMedicine.quantity }}{{ batchMedicine.unit }}</span>
        </div>
        <van-form class="batch-form" @submit="handleSubmitBatch">
          <div class="detail-card">
            <van-field
              v-model="batchForm.expiryDate"
              type="date"
              name="expiryDate"
              label="保质期"
              :rules="[{ required: true, message: '请选择保质期' }]"
            />
            <van-field
              v-model="batchQuantityInput"
              type="number"
              name="quantity"
              label="本次数量"
              placeholder="例如：2"
              :rules="[{ required: true, message: '请输入本次数量' }]"
            />
          </div>
          <div class="form-save-bar">
            <van-button block type="primary" native-type="submit">保存库存</van-button>
          </div>
        </van-form>
      </section>
    </van-popup>

    <van-popup v-model:show="showDetail" position="bottom" round class="sheet-popup">
      <section v-if="detailMedicine" class="detail-panel">
        <div class="sheet-title">
          <h2>{{ detailMedicine.name }}</h2>
          <van-button class="icon-close-button" icon="cross" size="small" plain @click="showDetail = false" />
        </div>
        <div class="detail-tags">
          <van-tag
            v-for="label in getMedicineStatus(detailMedicine).labels"
            :key="label.text"
            :type="label.type"
          >
            {{ label.text }}
          </van-tag>
        </div>
        <div v-if="detailImageUrl" class="detail-photo">
          <img :src="detailImageUrl" :alt="detailMedicine.name" @error="detailImageUrl = ''" />
        </div>
        <div class="detail-card">
          <van-cell title="分类" :value="detailMedicine.category" />
          <van-cell title="数量" :value="String(detailMedicine.quantity)" />
          <van-cell title="单位" :value="detailMedicine.unit" />
          <van-cell v-if="detailMedicine.location" title="存放位置" :value="detailMedicine.location" />
          <van-cell title="有效期" :value="detailMedicine.expiryDate" />
          <van-cell title="服用方法" :value="detailMedicine.dosageTiming || '不限'" />
          <van-cell v-if="detailMedicine.dosageCycle" title="用药周期" :value="detailMedicine.dosageCycle" />
          <div class="detail-note-row">
            <span>备注</span>
            <p>{{ detailMedicine.note || '无' }}</p>
          </div>
        </div>
      </section>
    </van-popup>

    <van-popup v-model:show="showHealthCheck" position="bottom" round class="sheet-popup">
      <MedicineHealthCheck
        :medicines="medicines"
        @close="showHealthCheck = false"
        @move-expired-to-recycle="handleMoveExpiredToRecycle"
      />
    </van-popup>

    <van-popup v-model:show="showCategoryManager" position="bottom" round class="sheet-popup">
      <section class="category-manager">
        <div class="sheet-title">
          <div>
            <p class="eyebrow">Category</p>
            <h2>管理分类</h2>
            <p>整理家庭药箱的分类名称</p>
          </div>
          <van-button class="icon-close-button" icon="cross" size="small" plain @click="showCategoryManager = false" />
        </div>
        <div class="category-card">
          <div class="category-add-row">
            <van-field v-model="newCategory" label="新增分类" placeholder="例如：眼耳鼻喉" />
            <van-button class="category-action-button" size="small" type="primary" @click="addCategory">新增</van-button>
          </div>
        </div>
        <div class="category-card category-edit-list">
          <van-cell v-for="category in categories" :key="category" :title="category">
            <template #right-icon>
              <van-button class="category-action-button" size="small" plain @click="startRenameCategory(category)">修改</van-button>
            </template>
          </van-cell>
        </div>
      </section>
    </van-popup>

    <van-popup v-model:show="showRecycleBin" position="bottom" round class="sheet-popup">
      <section class="recycle-panel">
        <div class="sheet-title">
          <div>
            <p class="eyebrow">Recycle Bin</p>
            <h2>回收站</h2>
            <p>恢复或永久删除已移入回收站的药品</p>
          </div>
          <van-button class="icon-close-button" icon="cross" size="small" plain @click="showRecycleBin = false" />
        </div>

        <section v-if="recycleLoading" class="loading-panel">
          <van-loading color="var(--color-primary)">正在加载回收站</van-loading>
        </section>
        <van-empty v-else-if="deletedMedicines.length === 0" description="回收站是空的" />
        <section v-else class="recycle-list">
          <RecycleMedicineCard
            v-for="medicine in deletedMedicines"
            :key="medicine._id"
            :medicine="medicine"
            @restore="handleRestoreMedicine"
            @permanent-delete="handlePermanentDelete"
          />
        </section>
      </section>
    </van-popup>

    <van-dialog
      v-model:show="showRenameDialog"
      title="修改分类名称"
      show-cancel-button
      @confirm="confirmRenameCategory"
    >
      <van-field v-model="renameCategoryValue" placeholder="请输入新的分类名称" />
    </van-dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { showConfirmDialog, showFailToast, showSuccessToast } from 'vant';
import GlobalActionBar from './components/GlobalActionBar.vue';
import MedicineHealthCheck from './components/MedicineHealthCheck.vue';
import MedicineCard from './components/MedicineCard.vue';
import MedicineForm from './components/MedicineForm.vue';
import RecycleMedicineCard from './components/RecycleMedicineCard.vue';
import { getCategoryAsset } from './categoryAssets';
import { DEFAULT_CATEGORIES, FAMILY_CODE_STORAGE_KEY } from './constants';
import { medicineApi } from './services/medicineApi';
import { resolveMedicineImageUrl } from './services/medicineStorage';
import type { Medicine, MedicineBatchInput, MedicineInput } from './types';
import {
  filterMedicines,
  getCategories,
  getMedicineStatus,
  groupByCategory,
} from './utils/medicine';

const familyCode = ref(localStorage.getItem(FAMILY_CODE_STORAGE_KEY) || '');
const CATEGORY_STORAGE_KEY = 'family_medicine_box_categories';
const codeInput = ref('');
const medicines = ref<Medicine[]>([]);
const deletedMedicines = ref<Medicine[]>([]);

function readStoredCategories() {
  try {
    const parsed = JSON.parse(localStorage.getItem(CATEGORY_STORAGE_KEY) || '[]');
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === 'string') : [];
  } catch {
    return [];
  }
}

const customCategories = ref<string[]>(readStoredCategories());
const keyword = ref('');
const activeTab = ref('home');
const expandedCategories = ref<string[]>([]);
const loading = ref(false);
const recycleLoading = ref(false);
const showForm = ref(false);
const formKey = ref(0);
const editingMedicine = ref<Medicine | null>(null);
const showDetail = ref(false);
const detailMedicine = ref<Medicine | null>(null);
const detailImageUrl = ref('');
const showBatchForm = ref(false);
const batchMedicine = ref<Medicine | null>(null);
const batchForm = reactive<MedicineBatchInput>({
  expiryDate: '',
  quantity: 1,
});
const batchQuantityInput = ref('1');
const showCategoryManager = ref(false);
const showHealthCheck = ref(false);
const showRecycleBin = ref(false);
const showMoreMenu = ref(false);
const newCategory = ref('');
const showRenameDialog = ref(false);
const renameCategorySource = ref('');
const renameCategoryValue = ref('');

const categories = computed(() => getCategories(medicines.value, customCategories.value));
const categoryGroups = computed(() => {
  const visible = filterMedicines(medicines.value, keyword.value, '全部', 'all');
  return groupByCategory(visible, categories.value);
});
const filteredMedicines = computed(() =>
  filterMedicines(medicines.value, keyword.value, '全部', 'all'),
);
const moreMenuActions = [{ text: '回收站', value: 'recycleBin' }];

function isDialogCancel(error: unknown) {
  return error === 'cancel' || error === 'overlay';
}

function isCategoryExpanded(category: string) {
  if (keyword.value.trim()) return true;
  return expandedCategories.value.includes(category);
}

function toggleCategory(category: string) {
  if (expandedCategories.value.includes(category)) {
    expandedCategories.value = expandedCategories.value.filter((item) => item !== category);
    return;
  }
  expandedCategories.value = [...expandedCategories.value, category];
}

async function loadMedicines() {
  if (!familyCode.value) return;
  loading.value = true;
  try {
    medicines.value = await medicineApi.list(familyCode.value);
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '加载失败');
  } finally {
    loading.value = false;
  }
}

async function loadDeletedMedicines() {
  if (!familyCode.value) return;
  recycleLoading.value = true;
  try {
    deletedMedicines.value = await medicineApi.listDeletedMedicines(familyCode.value);
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '回收站加载失败');
  } finally {
    recycleLoading.value = false;
  }
}

async function handleVerifyCode() {
  const value = codeInput.value.trim();
  if (!value) {
    showFailToast('请输入家庭访问码');
    return;
  }
  loading.value = true;
  try {
    await medicineApi.verifyFamilyCode(value);
    familyCode.value = value;
    localStorage.setItem(FAMILY_CODE_STORAGE_KEY, value);
    showSuccessToast('已进入家庭药箱');
    await loadMedicines();
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '访问码校验失败');
  } finally {
    loading.value = false;
  }
}

function resetCode() {
  localStorage.removeItem(FAMILY_CODE_STORAGE_KEY);
  familyCode.value = '';
  codeInput.value = '';
  medicines.value = [];
  deletedMedicines.value = [];
}

async function openRecycleBin() {
  showMoreMenu.value = false;
  showRecycleBin.value = true;
  await loadDeletedMedicines();
}

function handleMoreMenuSelect(action: { value?: string }) {
  if (action.value === 'recycleBin') {
    void openRecycleBin();
  }
}

function openCreateForm() {
  editingMedicine.value = null;
  formKey.value += 1;
  showForm.value = true;
}

function openEditForm(medicine: Medicine) {
  editingMedicine.value = medicine;
  formKey.value += 1;
  showForm.value = true;
}

function openDetail(medicine: Medicine) {
  detailMedicine.value = medicine;
  showDetail.value = true;
}

function openBatchForm(medicine: Medicine) {
  batchMedicine.value = medicine;
  batchForm.expiryDate = medicine.expiryDate;
  batchForm.quantity = 1;
  batchQuantityInput.value = '1';
  showBatchForm.value = true;
}

async function findMedicineForForm(name: string) {
  return medicineApi.findByName(familyCode.value, name);
}

async function recognizeMedicineImageForForm(imageUrl: string) {
  return medicineApi.aiRecognizeMedicine(familyCode.value, imageUrl);
}

async function handleSubmitMedicine(payload: MedicineInput, matchedMedicine: Medicine | null) {
  try {
    if (editingMedicine.value) {
      await medicineApi.update(familyCode.value, { ...payload, _id: editingMedicine.value._id });
      showSuccessToast('已更新药品');
    } else if (matchedMedicine) {
      if (payload.quantity <= 0) {
        showFailToast('本次数量必须大于 0');
        return;
      }
      await medicineApi.update(familyCode.value, {
        _id: matchedMedicine._id,
        category: payload.category,
        unit: payload.unit,
        note: payload.note,
        location: payload.location,
        imageUrl: payload.imageUrl,
        dosageTiming: payload.dosageTiming,
        dosageCycle: payload.dosageCycle,
      });
      await medicineApi.addBatch(familyCode.value, matchedMedicine._id, {
        expiryDate: payload.expiryDate,
        quantity: payload.quantity,
        createdAt: Date.now(),
      });
      showSuccessToast('已加入库存');
    } else {
      await medicineApi.add(familyCode.value, payload);
      showSuccessToast('已新增药品');
    }
    showForm.value = false;
    formKey.value += 1;
    await loadMedicines();
    if (!expandedCategories.value.includes(payload.category)) {
      expandedCategories.value = [...expandedCategories.value, payload.category];
    }
  } catch (error) {
    if (isDialogCancel(error)) return;
    showFailToast(error instanceof Error ? error.message : '保存失败');
  }
}

async function handleDelete(medicine: Medicine) {
  try {
    await showConfirmDialog({
      title: '删除药品',
      message: '删除后可在回收站恢复，确定删除吗？',
    });
    await medicineApi.delete(familyCode.value, medicine._id);
    showSuccessToast('已删除');
    await loadMedicines();
  } catch (error) {
    if (!isDialogCancel(error)) {
      showFailToast(error instanceof Error ? error.message : '删除失败');
    }
  }
}

async function handleMoveExpiredToRecycle(ids: string[]) {
  const selectedIds = Array.from(new Set(ids));
  if (selectedIds.length === 0) {
    showFailToast('请选择要清理的药品');
    return;
  }

  try {
    await showConfirmDialog({
      title: '移入回收站',
      message: `确认将 ${selectedIds.length} 个已过期药品移入回收站？\n移入后可在回收站恢复。`,
    });
    await Promise.all(selectedIds.map((id) => medicineApi.delete(familyCode.value, id)));
    showSuccessToast('已移入回收站');
    await loadMedicines();
  } catch (error) {
    if (!isDialogCancel(error)) {
      showFailToast(error instanceof Error ? error.message : '批量清理失败');
    }
  }
}

async function handleRestoreMedicine(medicine: Medicine) {
  try {
    await medicineApi.restoreMedicine(familyCode.value, medicine._id);
    showSuccessToast('已恢复');
    await Promise.all([loadMedicines(), loadDeletedMedicines()]);
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '恢复失败');
  }
}

async function handlePermanentDelete(medicine: Medicine) {
  try {
    await showConfirmDialog({
      title: '永久删除药品',
      message: '永久删除后无法恢复，确定吗？',
    });
    await medicineApi.permanentDeleteMedicine(familyCode.value, medicine._id);
    showSuccessToast('已永久删除');
    await loadDeletedMedicines();
  } catch (error) {
    if (!isDialogCancel(error)) {
      showFailToast(error instanceof Error ? error.message : '永久删除失败');
    }
  }
}

async function handleAdjustQuantity(medicine: Medicine, delta: -1) {
  try {
    await medicineApi.adjustQuantity(familyCode.value, medicine._id, delta);
    await loadMedicines();
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '库存更新失败');
  }
}

async function handleSubmitBatch() {
  if (!batchMedicine.value) return;
  const quantity = Math.max(1, Number(batchQuantityInput.value) || 1);
  try {
    await medicineApi.addBatch(familyCode.value, batchMedicine.value._id, {
      expiryDate: batchForm.expiryDate,
      quantity,
    });
    showBatchForm.value = false;
    showSuccessToast('已新增库存');
    await loadMedicines();
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '库存新增失败');
  }
}

async function handleUpdateBatch(medicine: Medicine, batchId: string, batch: MedicineBatchInput) {
  try {
    await medicineApi.updateBatch(familyCode.value, medicine._id, batchId, batch);
    await loadMedicines();
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '批次更新失败');
  }
}

async function handleDeleteBatch(medicine: Medicine, batchId: string) {
  try {
    await showConfirmDialog({
      title: '删除库存批次',
      message: '删除后会同步更新药品总库存，确定删除这一批吗？',
    });
    await medicineApi.deleteBatch(familyCode.value, medicine._id, batchId);
    showSuccessToast('已删除批次');
    await loadMedicines();
  } catch (error) {
    if (!isDialogCancel(error)) {
      showFailToast(error instanceof Error ? error.message : '批次删除失败');
    }
  }
}

function addCategory() {
  const value = newCategory.value.trim();
  if (!value) {
    showFailToast('请输入分类名称');
    return;
  }
  if (categories.value.includes(value)) {
    showFailToast('分类已存在');
    return;
  }
  customCategories.value.push(value);
  newCategory.value = '';
  showSuccessToast('分类已新增');
}

function startRenameCategory(category: string) {
  renameCategorySource.value = category;
  renameCategoryValue.value = category;
  showRenameDialog.value = true;
}

async function confirmRenameCategory() {
  const source = renameCategorySource.value;
  const target = renameCategoryValue.value.trim();
  if (!target || source === target) return;
  if (categories.value.includes(target)) {
    showFailToast('分类已存在');
    return;
  }

  const affected = medicines.value.filter((item) => item.category === source);
  try {
    await Promise.all(
      affected.map((item) =>
        medicineApi.update(familyCode.value, {
          _id: item._id,
          category: target,
        }),
      ),
    );
    customCategories.value = customCategories.value.map((item) => (item === source ? target : item));
    if (!DEFAULT_CATEGORIES.includes(source) && !customCategories.value.includes(target)) {
      customCategories.value.push(target);
    }
    await loadMedicines();
    showSuccessToast('分类已修改');
  } catch (error) {
    showFailToast(error instanceof Error ? error.message : '分类修改失败');
  }
}

onMounted(loadMedicines);

watch(
  customCategories,
  (value) => {
    localStorage.setItem(CATEGORY_STORAGE_KEY, JSON.stringify(value));
  },
  { deep: true },
);

let detailImageRequestId = 0;
watch(
  () => detailMedicine.value?.imageUrl,
  async (imageUrl) => {
    const requestId = ++detailImageRequestId;
    detailImageUrl.value = '';
    const resolved = await resolveMedicineImageUrl(imageUrl);
    if (requestId === detailImageRequestId) {
      detailImageUrl.value = resolved;
    }
  },
);
</script>
