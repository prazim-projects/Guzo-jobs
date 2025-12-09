<template>
  <ion-Footer translucent padding>
    <ion-toolbar color="primary">

      <ion-buttons slot="start">
        <ion-button @click="goHome">
          <ion-icon name="home"></ion-icon>
        </ion-button>
      </ion-buttons>

      <!-- <ion-title>GuzoMezgeb</ion-title> -->

      <ion-buttons slot="end">
        <ion-button @click="goProfile">
          <ion-icon name="contract"></ion-icon>
        </ion-button>
         <ion-button @click="mapET()">
          <ion-icon name="pin"></ion-icon>
        </ion-button>

      </ion-buttons>


    </ion-toolbar>
  </ion-Footer>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import {  IonFooter,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonIcon }
from '@ionic/vue';

const router = useRouter();

function goHome() {
  router.push('/home');
}

function mapET() {
  router.push('/mapET');
}

function goToAddNote() {
  router.push('/add');
}   

function goProfile() {
  router.push('/profile');
}
</script>
<style scoped></style>