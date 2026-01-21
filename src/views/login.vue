<template>
  <ion-page>
    <ion-header>
      <ion-toolbar color="primary">
        <ion-title>Login</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding" v-if="!userStore.isLoggedIn">
      <ion-card>
        <ion-card-header>
          <ion-card-title>Welcome Back!</ion-card-title>
          <ion-card-subtitle>Sign in to your account</ion-card-subtitle>
        </ion-card-header>

        <ion-card-content>
          <ion-item>
            <ion-label position="floating">Username</ion-label>
            <ion-input v-model="user.username" type="text" required></ion-input>
          </ion-item>

          <ion-item>
            <ion-label position="floating">Password</ion-label>
            <ion-input v-model="user.password" type="password" required></ion-input>
          </ion-item>

          <ion-button expand="block" @click="handleLogin" class="ion-margin-top">Login</ion-button>

          <p class="ion-text-center ion-margin-top">
            Don't have an account? <router-link to="/signup">Sign Up</router-link>
          </p>
        </ion-card-content>
      </ion-card>
    </ion-content>

    <ion-content v-else class="ion-padding">
      <ion-card>
        <ion-card-header>
          <ion-card-title>You are already logged in!</ion-card-title>
        </ion-card-header>
        <ion-card-content>
          <ion-button expand="block" @click="userStore.logout">Logout</ion-button>
          <ion-button expand="block" color="secondary" @click="router.push('/home')">Go to Home</ion-button>
        </ion-card-content>
      </ion-card>
    </ion-content>

    <ion-footer>
      <app-foot :routes="navRoutes" />
    </ion-footer>
  </ion-page>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/userStore'; // Assuming this is your Pinia store (similar to authStore)
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonItem,
  IonLabel,
  IonInput,
  IonButton,
  IonFooter,
} from '@ionic/vue';
import AppFoot from '@/components/appFoot.vue'; // Your footer component

const router = useRouter();
const userStore = useUserStore();

const navRoutes = [
  { path: '/', label: 'Home', icon: 'home-outline' },
  { path: '/add', label: 'Add Note', icon: 'add-circle-outline' },
  { path: '/login', label: 'Login', icon: 'log-in-outline' }, // Updated icon suggestion
  { path: '/profile', label: 'Profile', icon: 'person-circle-outline' },
  { path: '/mapET', label: 'Map ET', icon: 'map-outline' },
  { path: '/signup', label: 'Signup', icon: 'person-add-outline' },
];

const user = ref({
  username: '',
  password: '',
});

// const handleLogin = () => {
//   if (user.value.username && user.value.password) {
//     userStore.login({ username: user.value.username, password: user.value.password });
//     router.push('/home'); // Redirect to home after simulated login
//   } else {
//     // Optional: Add toast or alert for validation (using Ionic's alertController)
//     console.warn('Please fill in all fields');
//   }
// };
</script>

<style scoped>
ion-card {
  max-width: 400px;
  margin: 0 auto;
}
</style>