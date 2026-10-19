<template>
  <ion-page>
    <ion-header><ion-toolbar color="primary"><ion-title>{{ t('Sign Up') }}</ion-title></ion-toolbar></ion-header>
    <ion-content class="ion-padding">
      <form class="auth-form" @submit.prevent="handleSignup">
        <h1>{{ t('Create an Account') }}</h1>
        <ion-input v-model="user.username" :label="t('Username')" label-placement="stacked" fill="outline" autocomplete="username" required />
        <ion-input v-model="user.phone_number" :label="t('Phone Number')" label-placement="stacked" fill="outline" type="tel" autocomplete="tel" placeholder="+251" required />
        <ion-input v-model="user.email" :label="t('Email (for password recovery)')" label-placement="stacked" fill="outline" type="email" autocomplete="email" />
        <ion-input v-model="user.password" :label="t('Password')" label-placement="stacked" fill="outline" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" required />
        <p class="password-help">{{ t('password_rules') }}</p>
        <div class="password-actions">
          <ion-button fill="clear" type="button" :aria-label="t(showPassword ? 'Hide password' : 'Show password')" @click="showPassword = !showPassword"><ion-icon slot="icon-only" :icon="showPassword ? eyeOffOutline : eyeOutline" /></ion-button>
          <ion-button fill="clear" type="button" @click="generate">{{ t('Suggest a strong password') }}</ion-button>
        </div>
        <ion-input v-model="user.confirmPassword" :label="t('Confirm Password')" label-placement="stacked" fill="outline" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" required />
        <p v-if="user.confirmPassword && user.password !== user.confirmPassword" class="form-error" role="alert">{{ t('password_mismatch') }}</p>
        <p v-if="error" class="form-error" role="alert">{{ t(error) }}</p>
        <ion-button expand="block" type="submit" :disabled="busy">{{ t(busy ? 'Working...' : 'Sign Up') }}</ion-button>
        <ion-button expand="block" fill="outline" type="button" :disabled="busy" @click="handleFayda">Sign up with Fayda</ion-button>
        <p>{{ t('Already have an account?') }} <router-link to="/login">{{ t('Login') }}</router-link></p>
        <ion-button fill="clear" @click="toggleLanguage">{{ t(currentLanguage === 'en' ? 'lang_switch_to_am' : 'lang_switch_to_en') }}</ion-button>
      </form>
    </ion-content>
  </ion-page>
</template>
<script setup lang="ts">
defineOptions({ name: "RegisterPage" });
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { IonPage, IonHeader, IonToolbar, IonTitle, IonContent, IonInput, IonButton, IonIcon } from '@ionic/vue';
import { eyeOutline, eyeOffOutline } from 'ionicons/icons';
import { useAuthStore } from '@/stores/userStore';
import { t, authError, currentLanguage, toggleLanguage } from '@/utils/i18n';
import { isStrongPassword, suggestPassword } from '@/utils/password';
import '@/theme/auth.css';
import { startFayda } from '@/utils/fayda';
const router = useRouter();
const store = useAuthStore();
const user = ref({ username: '', phone_number: '', email: '', password: '', confirmPassword: '' });
const showPassword = ref(false);
const busy = ref(false);
const error = ref('');
async function handleFayda() {
  error.value = '';
  busy.value = true;
  try { await startFayda(); }
  catch { error.value = 'Could not start Fayda sign-up.'; }
  finally { busy.value = false; }
}
function generate() {
  user.value.password = suggestPassword();
  user.value.confirmPassword = user.value.password;
  showPassword.value = true;
  error.value = '';
}
async function handleSignup() {
  if (busy.value) return;
  error.value = '';
  const value = user.value;
  if (!value.username.trim() || !value.phone_number.trim()) { error.value = 'required_fields'; return; }
  if (value.password !== value.confirmPassword) { error.value = 'password_mismatch'; return; }
  if (!isStrongPassword(value.password)) { error.value = 'weak_password'; return; }
  busy.value = true;
  try {
    await store.register(value.username.trim(), value.phone_number.trim(), value.password, value.confirmPassword, value.email.trim());
    await router.replace('/profile');
  } catch (err) { error.value = authError(err); }
  finally { busy.value = false; }
}
</script>
