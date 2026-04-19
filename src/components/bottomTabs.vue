<template>
    <ion-tabs>
    <ion-router-outlet></ion-router-outlet>
      <ion-tab-bar id="main-tab-bar" slot="bottom">
        <ion-tab-button
          v-for="route in authTabs"
          :key="route.path"
          :tab="route.path.slice(1)"
          :href="route.path"
        >
        <ion-icon :name="route.icon"></ion-icon>
        <ion-label>{{ route.label }}</ion-label>
      </ion-tab-button>
        
    </ion-tab-bar>
  </ion-tabs>
</template>

<script setup lang="ts">
import { IonIcon, IonTabButton, IonTabs, IonTabBar, IonLabel, IonRouterOutlet } from '@ionic/vue';
import { useAuthStore } from '../stores/userStore';
import { computed } from 'vue';

const authStore = useAuthStore();

const navRoutes = [
  { path: '/home', label: 'Home', icon: 'home-outline' },

];


const authTabs = computed(() => {
  if (authStore.isAuthenticated) {
    return [
      ...navRoutes,  
      { path: '/myJobs', label: 'Jobs', icon: 'briefcase-outline' },
      { path: '/postJob', label: 'Post', icon: 'add-circle-outline' },
      { path: '/profile', label: 'Me', icon: 'person-circle-outline' },
  ]
  } else {
    return [
      ...navRoutes,
          { path: '/login', label: 'Login', icon: 'person-circle-outline' },
          { path: '/signup', label: 'Signup', icon: 'person-add-outline' },
     ]
    }
});

</script>

<style scoped>
ion-tab-bar {
  padding-bottom: env(safe-area-inset-bottom);
}

ion-label {
  font-size: 0.72rem;
}
</style>
