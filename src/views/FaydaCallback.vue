<template>
  <ion-page>
    <ion-content class="ion-padding">
      <div class="callback-state">
        <ion-spinner v-if="loading" name="crescent" />
        <p v-if="loading">Completing Fayda sign-in...</p>
        <p v-else role="alert">{{ error }}</p>
        <ion-button v-if="!loading" router-link="/login">Back to sign in</ion-button>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { IonButton, IonContent, IonPage, IonSpinner } from '@ionic/vue';
import { useAuthStore } from '@/stores/userStore';
import { faydaBackendUrl } from '@/utils/fayda';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const loading = ref(true);
const error = ref('');

onMounted(async () => {
  const ticket = typeof route.query.ticket === 'string' ? route.query.ticket : '';
  const providerError = route.query.error;
  window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}#/fayda/callback`);

  if (providerError || !ticket) {
    loading.value = false;
    error.value = providerError === 'cancelled'
      ? 'Fayda sign-in was cancelled.'
      : 'Fayda sign-in could not be completed. Please try again.';
    return;
  }

  try {
    const response = await fetch(faydaBackendUrl('/auth/fayda/complete/'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticket }),
    });
    if (!response.ok) throw new Error('Fayda ticket expired or was already used.');
    const session = await response.json();
    auth.acceptSession(session.token, session.user);
    localStorage.setItem('onboardingCompleted', 'true');
    await router.replace('/profile');
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'Fayda sign-in failed.';
    loading.value = false;
  }
});
</script>

<style scoped>
.callback-state {
  max-width: 26rem;
  margin: 20vh auto 0;
  text-align: center;
}
</style>
