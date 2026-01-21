<template>
  <ion-toolbar slot="bottom" color="primary">
    <ion-buttons slot="primary">
      <ion-button
        v-for="(route, index) in routes"
        :key="index"
        :router-link="route.path"
        fill="clear"
      >
        <ion-icon v-if="route.icon" :icon="route.icon" slot="icon-only" />
        <ion-label v-if="!route.icon">{{ route.label }}</ion-label> <!-- Optional: Show label if no icon -->
      </ion-button>
    </ion-buttons>
  </ion-toolbar>
</template>

<script setup lang="ts">
import { IonToolbar, IonButtons, IonButton, IonIcon, IonLabel } from '@ionic/vue';

interface RouteItem {
  path: string;
  label: string;
  icon?: string;
}

defineProps<{
  routes: RouteItem[];
}>();
</script>

<style scoped>
/* Make it look like tabs: Even spacing, etc. */
ion-toolbar {
  --padding-start: 0;
  --padding-end: 0;
}

ion-buttons {
  justify-content: space-around;
  width: 100%;
}

ion-button {
  flex: 1;
  --color: var(--ion-color-contrast);
  --color-activated: var(--ion-color-light);
}
</style>