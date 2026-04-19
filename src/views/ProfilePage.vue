<template>
  <ion-page>
    <ion-header>
      <ion-toolbar color="primary">
        <ion-title>My Profile</ion-title>
        <ion-buttons slot="end">
          <ion-button v-if="!isEditing" @click="startEditing">
            <ion-icon slot="icon-only" :icon="pencil"></ion-icon>
          </ion-button>
          <ion-button v-if="isEditing" @click="cancelEdit">
            <ion-icon slot="icon-only" :icon="close"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content :fullscreen="true" class="ion-padding">
      <ion-refresher slot="fixed" @ionRefresh="doRefresh($event)">
        <ion-refresher-content pulling-text="Pull to refresh" refreshing-spinner="circles" refreshing-text="Updating data..."></ion-refresher-content>
      </ion-refresher>
      <!-- Loading -->
      <div v-if="loading || updating" class="ion-text-center ion-padding">
        <ion-spinner name="crescent"></ion-spinner>
        <p>{{ updating ? 'Saving profile...' : 'Loading profile...' }}</p>
      </div>

      <!-- Error -->
      <ion-card v-else-if="error || updateError" color="danger">
        <ion-card-content class="ion-text-center">
          <p>{{ error?.message || updateErrorMessage || 'Failed to load/save profile' }}</p>
          <ion-button color="light" @click="refetch">Retry</ion-button>
        </ion-card-content>
      </ion-card>

      <!-- Profile Content -->
      <div v-else-if="userData">
        <ion-card class="profile-card ion-margin-bottom">
          <ion-card-header class="ion-text-center">
            <ion-avatar class="profile-avatar">
              <img :src="form.profilePicture || defaultAvatar" alt="Profile picture" />
            </ion-avatar>
            <ion-card-title class="profile-name">{{ userData.username }}</ion-card-title>
            <ion-card-subtitle>{{ userData.email || 'No email set' }}</ion-card-subtitle>
          </ion-card-header>

          <ion-card-content>
            <ion-list lines="inset">
              <!-- Email -->
              <ion-item>
                <ion-label position="stacked">Email</ion-label>
                <ion-input
                  v-if="isEditing"
                  v-model="form.email"
                  type="email"
                  placeholder="your.email@example.com"
                  autofocus
                ></ion-input>
                <ion-label v-else>{{ form.email || 'Not set' }}</ion-label>
              </ion-item>

              <!-- Phone Number -->
              <ion-item>
                <ion-label position="stacked">Phone Number</ion-label>
                <ion-input
                  v-if="isEditing"
                  v-model="form.phoneNumber"
                  type="tel"
                  placeholder="+251 9xx xxx xxx"
                ></ion-input>
                <ion-label v-else>{{ form.phoneNumber || 'Not set' }}</ion-label>
              </ion-item>

              <!-- Bio -->
              <ion-item>
                <ion-label position="stacked">Bio</ion-label>
                <ion-textarea
                  v-if="isEditing"
                  v-model="form.bio"
                  :rows="5"
                  auto-grow
                  placeholder="Write something about yourself..."
                ></ion-textarea>
                <ion-label v-else class="ion-text-wrap">
                  {{ form.bio || 'No bio yet' }}
                </ion-label>
              </ion-item>

              <!-- Profile Picture URL -->
              <ion-item>
                <ion-label position="stacked">Profile Picture URL</ion-label>
                <ion-input
                  v-if="isEditing"
                  v-model="form.profilePicture"
                  placeholder="https://example.com/your-photo.jpg"
                ></ion-input>
                <ion-label v-else class="ion-text-wrap">
                  {{ form.profilePicture ? 'Image set' : 'No picture' }}
                </ion-label>
              </ion-item>

              <!-- Preview (only in edit mode) -->
              <div v-if="isEditing && form.profilePicture" class="ion-margin-top ion-text-center">
                <ion-img :src="form.profilePicture" class="preview-img" alt="Preview" />
                <p class="ion-text-small">Preview</p>
              </div>
            </ion-list>

            <!-- Action Buttons (edit mode only) -->
            <div v-if="isEditing" class="ion-margin-top ion-text-center">
              <ion-button expand="block" color="success" @click="saveProfile" :disabled="updating || !isFormValid">
                Save Changes
              </ion-button>
              <ion-button expand="block" fill="clear" @click="cancelEdit" :disabled="updating">
                Cancel
              </ion-button>
            </div>
          </ion-card-content>
        </ion-card>

        <ion-card>
          <ion-card-header>
            <ion-card-title>Quick Actions</ion-card-title>
          </ion-card-header>
          <ion-card-content>
            <ion-button expand="block" fill="outline" @click="switchLanguage">{{ languageButtonLabel }}</ion-button>
            <ion-button expand="block" fill="outline" router-link="/notifications" class="notification-quick-action">
              Notifications
              <ion-badge v-if="unreadNotificationsCount > 0" color="danger" class="quick-action-badge">
                {{ unreadNotificationsCount }}
              </ion-badge>
            </ion-button>
            <ion-button expand="block" fill="outline" router-link="/support">Support</ion-button>
            <ion-button expand="block" fill="outline" router-link="/mapET">Map</ion-button>
            <ion-button expand="block" color="medium" router-link="/logout">Logout</ion-button>
          </ion-card-content>
        </ion-card>

        <ion-card class="ion-margin-top">
          <ion-card-header>
            <ion-card-title>Platform Transaction Summary</ion-card-title>
          </ion-card-header>
          <ion-card-content>
            <p><strong>Total Paid to Escrow:</strong> {{ transactionSummary.totalPaid.toFixed(2) }} Birr</p>
            <p><strong>Total Received (Released):</strong> {{ transactionSummary.totalReceived.toFixed(2) }} Birr</p>
            <p><strong>Total Transacted:</strong> {{ transactionSummary.totalTransacted.toFixed(2) }} Birr</p>
          </ion-card-content>
        </ion-card>
      </div>

      <!-- Not Logged In -->
      <div v-else class="ion-text-center ion-padding">
        <ion-icon :icon="alertCircleOutline" size="large" color="warning"></ion-icon>
        <p>Please log in to view and edit your profile.</p>
        <ion-button expand="block" router-link="/login">Go to Login</ion-button>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import { gql } from '@apollo/client/core'
import { useAuthStore } from '@/stores/userStore'
import { useToast } from '@/composables/useToast'
import { currentLanguage, t, toggleLanguage } from '@/utils/i18n'
import {
  IonPage, IonHeader, IonToolbar, IonTitle, IonContent, IonCard, IonCardHeader,
  IonCardTitle, IonCardSubtitle, IonCardContent, IonList, IonItem, IonLabel,
  IonInput, IonTextarea, IonButton, IonButtons, IonAvatar, IonIcon, IonSpinner,
  IonImg, IonRefresher, IonRefresherContent, RefresherCustomEvent, toastController
} from '@ionic/vue'
import { useRouter } from 'vue-router'
import { pencil, close, alertCircleOutline } from 'ionicons/icons'

const router = useRouter()

// GraphQL
const GET_USER = gql`
  query GetCurrentUser($id: ID!) {
    userById(id: $id) {
      id
      username
      email
      phoneNumber
      bio
      profilePicture
    }
    myTransactionSummary {
      totalPaid
      totalReceived
      totalTransacted
    }
  }
`

const UPDATE_PROFILE = gql`
  mutation EditProfile($bio: String, $email: String, $phoneNumber: String, $profilePicture: String) {
    editProfile(bio: $bio, email: $email, phoneNumber: $phoneNumber, profilePicture: $profilePicture) {
      user {
        id
        username
        email
        phoneNumber
        bio
        profilePicture
      }
    }
  }
`

const MY_NOTIFICATIONS = gql`
  query MyNotificationsForBadge {
    myNotifications {
      id
      isRead
    }
  }
`

const authStore = useAuthStore()
const toast = useToast()

const userId = computed(() => authStore.user?.id)

// Query
const { result, loading, error, refetch } = useQuery(GET_USER, () => ({
  id: userId.value
}), () => ({
  enabled: !!userId.value
}))

const { result: notificationResult, refetch: refetchNotifications } = useQuery(MY_NOTIFICATIONS, null, {
  fetchPolicy: 'cache-first',
})



const { mutate: editProfile, onDone, onError } = useMutation(UPDATE_PROFILE);

const updating = ref(false)
const updateError = ref<Error | null>(null)
const updateErrorMessage = computed(() => updateError.value?.message || '')

onDone(async () => {
  updating.value = false
  updateError.value = null
  toast?.success('Profile updated successfully!')
  isEditing.value = false
  refetch() // Refresh query
  router.replace('/home');
});

onError(async (error) => {
  updating.value = false
  updateError.value = error
  const toast = await toastController.create({ message: error.message, duration: 3000, color: 'danger' });
  await toast.present();
});



// Form & Edit Mode

const isEditing = ref(false)
const form = ref({
  email: '',
  phoneNumber: '',
  bio: '',
  profilePicture: ''
})

const userData = computed(() => result.value?.userById)
const unreadNotificationsCount = computed(() => {
  const list = notificationResult.value?.myNotifications || []
  return list.filter((item: { isRead: boolean }) => !item.isRead).length
})

const transactionSummary = computed(() => {
  const summary = result.value?.myTransactionSummary
  return {
    totalPaid: Number(summary?.totalPaid || 0),
    totalReceived: Number(summary?.totalReceived || 0),
    totalTransacted: Number(summary?.totalTransacted || 0),
  }
})

const languageButtonLabel = computed(() => {
  return currentLanguage.value === 'en' ? t('lang_switch_to_am') : t('lang_switch_to_en')
})

const switchLanguage = async () => {
  toggleLanguage()
  const notice = await toastController.create({
    message: t('refresh_notice'),
    duration: 2200,
    color: 'primary',
    position: 'bottom',
    positionAnchor: 'main-tab-bar',
  })
  await notice.present()
}

const doRefresh = async (event: RefresherCustomEvent) => {
  try {
    await Promise.all([refetch(), refetchNotifications()])
    const notice = await toastController.create({
      message: `${t('refresh_done')} ${t('refresh_notice')}`,
      duration: 2200,
      color: 'success',
      position: 'bottom',
      positionAnchor: 'main-tab-bar',
    })
    await notice.present()
  } finally {
    event.target.complete()
  }
}

// Sync form when data loads
watch(userData, (newUser) => {
  if (newUser) {
    form.value = {
      email: newUser.email || '',
      phoneNumber: newUser.phoneNumber || '',
      bio: newUser.bio || '',
      profilePicture: newUser.profilePicture || ''
    }
  }
}, { immediate: true })

// Simple validation (optional – expand as needed)
const isFormValid = computed(() => {
  if (!isEditing.value) return true
  return form.value.email.includes('@') || !form.value.email // basic email check
})

// Start / Cancel
function startEditing() {
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
  // Reset to original
  if (userData.value) {
    form.value = {
      email: userData.value.email || '',
      phoneNumber: userData.value.phoneNumber || '',
      bio: userData.value.bio || '',
      profilePicture: userData.value.profilePicture || ''
    }
  }
}

// Save
async function saveProfile() {
  if (!userId.value) return

  updating.value = true
  updateError.value = null

  try {
    await editProfile({
      bio: form.value.bio || null,
      email: form.value.email || null,
      phoneNumber: form.value.phoneNumber || null,
      profilePicture: form.value.profilePicture || null
    })
  } catch (err) {
    updating.value = false
    updateError.value = err instanceof Error ? err : new Error(String(err))
    toast?.error('Failed to update profile')
    console.error(err)
  }
}

// Avatar fallback
const defaultAvatar = 'https://ui-avatars.com/api/?name=User&background=random'
</script>

<style scoped>
.profile-card {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  margin-bottom: 24px;
}

.profile-avatar {
  width: 100px;
  height: 100px;
  margin: 24px auto 16px;
  border: 4px solid var(--ion-color-primary);
  border-radius: 50%;
  overflow: hidden;
}

.preview-img {
  max-width: 200px;
  max-height: 200px;
  border-radius: 12px;
  object-fit: cover;
  border: 1px solid var(--ion-color-medium);
}

.profile-name {
  font-size: 1.8rem;
  font-weight: bold;
}

.notification-quick-action {
  position: relative;
}

.quick-action-badge {
  margin-left: 8px;
}
</style>