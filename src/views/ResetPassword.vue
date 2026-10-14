<template>
  <ion-page>
    <ion-header><ion-toolbar><ion-title>{{ t('Reset Password') }}</ion-title></ion-toolbar></ion-header>
    <ion-content class="ion-padding">
      <form class="auth-form" @submit.prevent="submit">
        <p v-if="!hasToken">{{ t('recovery_help') }}</p>
        <template v-if="hasToken">
          <ion-input v-model="password" :label="t('Password')" label-placement="stacked" fill="outline" type="password" autocomplete="new-password" required />
          <p class="password-help">{{ t('password_rules') }}</p>
          <ion-input v-model="confirmation" :label="t('Confirm Password')" label-placement="stacked" fill="outline" type="password" autocomplete="new-password" required />
        </template>
        <ion-input v-else v-model="email" :label="t('Email')" label-placement="stacked" fill="outline" type="email" autocomplete="email" required />
        <p v-if="error" class="form-error" role="alert">{{ t(error) }}</p>
        <p v-if="success" role="status">{{ t(success) }}</p>
        <ion-button expand="block" type="submit" :disabled="busy || success === 'reset_done'">{{ t(busy ? 'Working...' : hasToken ? 'Reset Password' : 'Send Reset Link') }}</ion-button>
        <ion-button fill="clear" router-link="/login">{{ t('Go to Login') }}</ion-button>
      </form>
    </ion-content>
  </ion-page>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useApolloClient } from '@vue/apollo-composable';
import { gql } from '@apollo/client/core';
import { IonPage, IonHeader, IonToolbar, IonTitle, IonContent, IonInput, IonButton } from '@ionic/vue';
import { t, authError } from '@/utils/i18n';
import { isStrongPassword } from '@/utils/password';
import '@/theme/auth.css';
const route = useRoute();
const { client } = useApolloClient();
const hasToken = computed(() => !!route.query.uid && !!route.query.token);
const email = ref('');
const password = ref('');
const confirmation = ref('');
const error = ref('');
const success = ref('');
const busy = ref(false);
async function submit() {
  if (busy.value) return;
  error.value = ''; success.value = '';
  if (hasToken.value && password.value !== confirmation.value) { error.value = 'password_mismatch'; return; }
  if (hasToken.value && !isStrongPassword(password.value)) { error.value = 'weak_password'; return; }
  busy.value = true;
  try {
    if (hasToken.value) {
      await client.mutate({ mutation: gql`mutation Reset($uid: String!, $token: String!, $password: String!, $confirmPassword: String!) { resetPassword(uid: $uid, token: $token, password: $password, confirmPassword: $confirmPassword) { success } }`, variables: { uid: route.query.uid, token: route.query.token, password: password.value, confirmPassword: confirmation.value } });
      password.value = ''; confirmation.value = ''; success.value = 'reset_done';
    } else {
      await client.mutate({ mutation: gql`mutation RequestReset($email: String!) { requestPasswordReset(email: $email) { success } }`, variables: { email: email.value.trim() } });
      success.value = 'reset_sent';
    }
  } catch (err) { error.value = authError(err); }
  finally { busy.value = false; }
}
</script>
