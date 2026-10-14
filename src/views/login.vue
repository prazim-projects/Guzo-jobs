<template>
  <ion-page>
    <ion-header>
      <ion-toolbar color="primary">
        <ion-title>{{ t("Login") }}</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding" v-if="!userStore.isAuthenticated">
      <ion-card>
        <ion-card-header>
          <ion-card-title>{{ t("Welcome Back!") }}</ion-card-title>
          <ion-card-subtitle>{{ t("Sign in to your account") }}</ion-card-subtitle>
        </ion-card-header>

        <ion-card-content>
          <ion-item>
            <ion-label position="floating">{{ t("Username") }}</ion-label>
            <ion-input v-model="user.username" type="text" required></ion-input>
          </ion-item>

          <ion-item>
            <ion-label position="floating">{{ t("Password") }}</ion-label>
            <ion-input v-model="user.password" :type="showPassword ? 'text' : 'password'" required></ion-input>
            <ion-button
              slot="end"
              fill="clear"
              size="small"
              type="button"
              :aria-label="t(showPassword ? 'Hide password' : 'Show password')"
              @click="showPassword = !showPassword"
            >
              <ion-icon :icon="showPassword ? eyeOffOutline : eyeOutline"></ion-icon>
            </ion-button>
          </ion-item>

          <p v-if="loginError" class="form-error" role="alert">{{ t(loginError) }}</p>
          <ion-button expand="block" @click="handleLogin" :disabled="busy" class="ion-margin-top">{{ t(busy ? 'Working...' : 'Login') }}</ion-button>
          <ion-button expand="block" fill="clear" router-link="/reset-password">{{ t('Forgot password?') }}</ion-button>
          <ion-button expand="block" fill="clear" @click="toggleLanguage">{{ t(currentLanguage === 'en' ? 'lang_switch_to_am' : 'lang_switch_to_en') }}</ion-button>

          <p class="ion-text-center ion-margin-top">
            {{ t("Don't have an account?") }} <router-link to="/signup">{{ t("Sign Up") }}</router-link>
          </p>
        </ion-card-content>
      </ion-card>
    </ion-content>

    <ion-content v-else class="ion-padding">
      <ion-card>
        <ion-card-header>
          <ion-card-title>{{ t("You are already logged in!") }}</ion-card-title>
        </ion-card-header>
        <ion-card-content>
          <ion-button expand="block" @click="userStore.logout">{{ t("Logout") }}</ion-button>
          <ion-button expand="block" color="secondary" @click="router.push('/home')">{{ t("Go to Home") }}</ion-button>
        </ion-card-content>
      </ion-card>
    </ion-content>

  </ion-page>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { t, authError, currentLanguage, toggleLanguage } from '@/utils/i18n';
import '@/theme/auth.css';
import { useRouter } from 'vue-router';
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
  IonIcon,
} from '@ionic/vue';
import { eyeOffOutline, eyeOutline } from 'ionicons/icons';
import { useAuthStore } from '@/stores/userStore';

const router = useRouter();
const userStore = useAuthStore();

const user = ref({
  username: '',
  password: '',
});

const showPassword = ref(false);
const loginError = ref('');
const busy = ref(false);


const handleLogin = async () => {
  if (busy.value) return;
  loginError.value = '';
  if (!user.value.username.trim() || !user.value.password) { loginError.value = 'required_fields'; return; }
  busy.value = true;
  try {
    await userStore.login(user.value.username, user.value.password)
    router.push('/');
  } catch (err) {
    loginError.value = authError(err, (err as { networkError?: unknown })?.networkError ? 'request_failed' : 'invalid_credentials');
  } finally {
    busy.value = false;
  }
}

</script>

<style scoped>
ion-card {
  max-width: 400px;
  margin: 0 auto;
}
</style>
