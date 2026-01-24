<template>
  <ion-app>
    <ion-tabs>
    <ion-router-outlet></ion-router-outlet>
    <ion-tab-bar slot="bottom">
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
  </ion-app>
</template>

<script setup type="ts">
import { IonIcon, IonTabButton, IonTabs, IonTabBar, IonLabel, IonApp, IonRouterOutlet, IonDatetimeButton } from '@ionic/vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from './stores/userStore';
import { computed } from 'vue';

const authStore = useAuthStore();

const navRoutes = [
  { path: '/home', label: 'Home', icon: 'home-outline' },

];


const authTabs = computed(() => {
  if (authStore.isAuthenticated) {
    return [
      ...navRoutes,  
        { path: '/postJob', label: 'Post Job', icon: 'add-circle-outline' },
        { path: '/profile', label: 'Profile', icon: 'person-circle-outline' },
        { path: '/mapET', label: 'Map ET', icon: 'map-outline' },
        {path: '/logout', label: 'Logout', icon: 'log-out-outline' },
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
