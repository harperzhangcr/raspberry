<template>
  <section class="global-action-bar">
    <van-button icon="plus" type="primary" @click="$emit('add-medicine')">新增药品</van-button>
    <van-button
      class="global-action-bar__check"
      icon="records-o"
      plain
      type="primary"
      @click="$emit('open-health-check')"
    >
      药箱体检
    </van-button>
  </section>
</template>

<script setup lang="ts">
defineEmits<{
  'add-medicine': [];
  'open-health-check': [];
}>();
</script>

<style scoped>
.global-action-bar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-sm);
  padding: var(--space-lg) 0 var(--space-sm);
}

.global-action-bar :deep(.van-button) {
  min-height: 48px;
}

.global-action-bar :deep(.global-action-bar__check.van-button) {
  border: 0;
  background: rgba(255, 255, 255, 0.68);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.82),
    inset 0 -1px 0 rgba(20, 122, 255, 0.08);
}
</style>
