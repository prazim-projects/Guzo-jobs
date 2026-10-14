<template>
  <ion-button expand="block" fill="outline" router-link="/reset-password">{{ t('Reset Password') }}</ion-button>
  <ion-button expand="block" color="danger" fill="outline" @click="showDelete = true">{{ t('Delete Account') }}</ion-button>
  <ion-modal :is-open="showDelete" @didDismiss="close">
    <ion-header><ion-toolbar><ion-title>{{ t('Delete Account') }}</ion-title></ion-toolbar></ion-header>
    <ion-content class="ion-padding">
      <form class="auth-form" @submit.prevent="remove">
        <p>{{ t('delete_warning') }}</p>
        <ion-input v-model="password" :label="t('Password')" label-placement="stacked" fill="outline" type="password" autocomplete="current-password" required />
        <p v-if="error" role="alert" class="form-error">{{ t(error) }}</p>
        <ion-button type="submit" expand="block" color="danger" :disabled="busy || !password">{{ t(busy ? 'Working...' : 'Delete Account') }}</ion-button>
        <ion-button expand="block" fill="clear" :disabled="busy" @click="close">{{ t('Cancel') }}</ion-button>
      </form>
    </ion-content>
  </ion-modal>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import { IonButton, IonModal, IonHeader, IonToolbar, IonTitle, IonContent, IonInput } from '@ionic/vue';
import { useApolloClient } from '@vue/apollo-composable';
import { gql } from '@apollo/client/core';
import { useAuthStore } from '@/stores/userStore';
import { t, authError } from '@/utils/i18n';
import '@/theme/auth.css';
const { client } = useApolloClient();
const store = useAuthStore();
const showDelete = ref(false);
const password = ref('');
const error = ref('');
const busy = ref(false);
function close() { showDelete.value = false; password.value = ''; error.value = ''; }
async function remove() {
  if (busy.value || !password.value) return;
  busy.value = true; error.value = '';
  try {
    await client.mutate({ mutation: gql`mutation DeleteAccount($password: String!) { deleteAccount(password: $password) { success } }`, variables: { password: password.value } });
    close(); store.logout();
  } catch (err) { error.value = authError(err); }
  finally { busy.value = false; }
}
</script>
