<script lang="ts" setup>
import { IonPage, IonContent, IonButton, IonHeader, IonToolbar, IonTitle, IonButtons, IonBackButton } from '@ionic/vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/userStore';

const userStore = useAuthStore()
const router = useRouter();

const handleLogout = async () => {
  try {
    await userStore.logout();
    
    router.replace('/'); 
  } catch (error) {
    console.error("Logout failed", error);
  }
};

</script>

<template>
    <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/profile"></ion-back-button>
        </ion-buttons>
        <ion-title>Logout</ion-title>
      </ion-toolbar>
    </ion-header>
        <ion-content class="ion-padding">
            <h1>Logout Page</h1>
            <p>Are you sure you want to logout?</p>
            <ion-button @click="handleLogout">
                Confirm Logout
            </ion-button>
            <IonButton fill="clear" @click="router.back()">
                Cancel
            </IonButton>
        </ion-content>
    </ion-page>

</template>