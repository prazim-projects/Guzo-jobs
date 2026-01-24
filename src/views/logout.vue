<script lang="ts" setup>
import { IonPage, IonContent, IonButton } from '@ionic/vue';
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