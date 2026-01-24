<script lang="ts" setup>
import { useRouter } from 'vue-router';
import { IonContent, IonPage } from '@ionic/vue';


const router = useRouter();

const navRoutes = [
  { path: '/', label: 'Home', icon: 'home-outline' },
  { path: '/add', label: 'Add Note', icon: 'add-circle-outline' },
  { path: '/login', label: 'Login', icon: 'log-in-outline' },
  { path: '/profile', label: 'Profile', icon: 'person-circle-outline' },
  { path: '/mapET', label: 'Map ET', icon: 'map-outline' },
  { path: '/signup', label: 'Signup', icon: 'person-add-outline' },
];

</script>

<template>
    <ion-page>
        <ion-content ion-padding>
            <h1>Profile Page</h1>
            <p>This is the profile page.</p>
        </ion-content>
    </ion-page>
</template>


