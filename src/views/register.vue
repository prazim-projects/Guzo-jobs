<template>
  <ion-page>
    <ion-header>
      <ion-toolbar color="primary">
        <ion-title>Sign Up</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <ion-card>
        <ion-card-header>
          <ion-card-title>Create an Account</ion-card-title>
          <ion-card-subtitle>Join Guzo Jobs today!</ion-card-subtitle>
        </ion-card-header>

        <ion-card-content>
          <ion-item>
            <ion-label position="floating">Username</ion-label>
            <ion-input v-model="user.username" type="text" required></ion-input>
          </ion-item>

          <ion-item>
            <ion-label position="floating">Email</ion-label>
            <ion-input v-model="user.email" type="email" required></ion-input>
          </ion-item>

          <ion-item>
            <ion-label position="floating">Password</ion-label>
            <ion-input v-model="user.password" type="password" required></ion-input>
          </ion-item>

          <ion-item>
            <ion-label position="floating">Confirm Password</ion-label>
            <ion-input v-model="user.confirmPassword" type="password" required></ion-input>
          </ion-item>

          <ion-button expand="block" @click="handleSignup" class="ion-margin-top">Sign Up</ion-button>

          <p class="ion-text-center ion-margin-top">
            Already have an account? <router-link to="/login">Login</router-link>
          </p>
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
import { useUserStore } from '@/stores/userStore'; // Assuming this is your Pinia store
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
  { path: '/login', label: 'Login', icon: 'log-in-outline' },
  { path: '/profile', label: 'Profile', icon: 'person-circle-outline' },
  { path: '/mapET', label: 'Map ET', icon: 'map-outline' },
  { path: '/signup', label: 'Signup', icon: 'person-add-outline' },
];

const user = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
});

// const handleSignup = () => {
//   if (user.value.username && user.value.email && user.value.password && user.value.password === user.value.confirmPassword) {
//     userStore.register({ username: user.value.username, email: user.value.email, password: user.value.password });
//     router.push('/login'); // Redirect to login after simulated signup
//   } else {
//     // Optional: Add toast or alert for validation
//     console.warn('Please fill in all fields correctly');
//   }
// };
</script>

<style scoped>
ion-card {
  max-width: 400px;
  margin: 0 auto;
}
</style>