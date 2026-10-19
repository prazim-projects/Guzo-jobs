<template>
  <ion-page><OnboardingContent @complete="complete" /></ion-page>
</template>

<script setup lang="ts">
defineOptions({ name: 'OnboardingPage' });
import { IonPage } from '@ionic/vue';
import { useRouter } from 'vue-router';
import OnboardingContent from '@/components/OnboardingContent.vue';
const router = useRouter();
function complete() {
  localStorage.setItem('onboardingCompleted', 'true');
  void router.replace('/home');
}
</script>
