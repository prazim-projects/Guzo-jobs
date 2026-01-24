<template>
  <ion-page>
    <ion-content>
  <ion-refresher slot="fixed" @ionRefresh="doRefresh($event)">
    <ion-refresher-content 
      pulling-text="Pull to refresh" 
      refreshing-spinner="circles"
      refreshing-text="Updating data...">
    </ion-refresher-content>
  </ion-refresher>

  <div class="ion-padding">
    <div class="hero ion-padding">
      <h1 class="title">Welcome to Guzo Jobs 🌍</h1>
      <p class="subtitle">Odd job for travellers!</p>
    </div>
  </div>

  <!-- Jobs List -->
  <ion-grid v-if="!loading && !error && result?.availableJobs?.length">
    <ion-row>
      <ion-col size="12" size-md="6" size-sm="4" v-for="job in result.availableJobs" :key="job.id">
        <ion-card class="job-card">
          <!-- Dynamic Image -->
          <img
            :src="`https://picsum.photos/seed/${encodeURIComponent(job.destination)}/500/300`"
            :alt="'Image for trip to ' + job.destination"
            class="card-image"
          />

          <ion-card-header>
            <ion-card-title>{{ job.description.substring(0, 60) + '...' }}</ion-card-title>
            <ion-card-subtitle>
              <ion-icon name="location-outline" size="small"></ion-icon>
              Origin Location: {{ job.origin }}
            </ion-card-subtitle>
          </ion-card-header>

          <ion-card-content>
            <p><strong>Going To:</strong> {{ job.destination }}</p>
            <p v-if="job.expiresAt">
              <ion-icon name="time-outline" size="small"></ion-icon>
              Expires: {{ formatDate(job.expiresAt) }}
            </p>
          </ion-card-content>

          <!-- AUTHENTICATED USER SECTION -->
          <ion-item v-if="job.user" lines="none" class="user-info-item">
            <ion-avatar slot="start">
              <img :src="job.user.profilePicture || 'https://ionicframework.com'" />
            </ion-avatar>
            <ion-label>
              <h3>{{ job.user.username }}</h3>
              <p v-if="job.user.phoneNumber">
                <ion-icon name="call-outline"></ion-icon> {{ job.user.phoneNumber }}
              </p>
              <em><p> price: {{ job.price }}</p></em>
            </ion-label>
            <!-- Native call button -->
            <ion-button v-if="job.user.phoneNumber" slot="end" fill="clear" :href="'tel:' + job.user.phoneNumber">
              <ion-icon slot="icon-only" name="call"></ion-icon>
            </ion-button>
          </ion-item>
          <div class="ion-padding-horizontal ion-padding-bottom">
            <ion-button 
              expand="block" 
              color="success" 
              class="ion-no-margin"
              @click="handleAcceptJob(job.id, 'PENDING')"
              v-if="job.user && job.user.id !== authStore.user?.id">
                <ion-icon slot="start" :icon="checkmarkCircle"></ion-icon>
                Accept Job
              </ion-button>
    
            <ion-badge v-else-if="job.user" color="light" expand="block" mode="ios" class="full-width-badge">
              Your Post
            </ion-badge>
          </div>
          <div v-if="job.user?.id === authStore.user?.id && job.contract?.status === 'PENDING'" class="ion-padding approval-box">
            <ion-item lines="none" color="light">
              <ion-icon slot="start" :icon="alertCircleOutline" color="warning"></ion-icon>
              <ion-label>
                <h3>Pending Acceptance</h3>
                <p>{{ job.contract.acceptor.username }} wants to do this job.</p>
              </ion-label>
            </ion-item>
            
            <ion-button expand="block" color="primary" @click="handleJobConfirmation(job.id, job.user?.id)">
              Confirm {{ job.contract.acceptor.username }}
            </ion-button>
          </div>
        </ion-card>
      </ion-col>
    </ion-row>
  </ion-grid>

  <ion-text v-if="loading" class="ion-padding ion-text-center">Loading...</ion-text>
  <ion-text v-if="error" color="danger" class="ion-padding">Error: {{ error.message }}</ion-text>
</ion-content>

    
  </ion-page>
</template>

<script lang="ts" setup>
// import floatingPostButton from '@/components/floatingPostButton.vue'
import { gql } from '@apollo/client/core'
import { useApolloClient } from '@vue/apollo-composable'
import { useQuery } from '@vue/apollo-composable'
import { format } from 'date-fns'
import {
  IonAvatar,
  IonPage,
  IonLabel,
  IonContent,
  IonBadge,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonGrid,
  IonRow, 
  IonCol,
  IonIcon,
  IonText,
  IonButton,
  IonButtons,
  IonRefresher,
  IonRefresherContent,
  RefresherCustomEvent,
  toastController,
  IonItem
} from '@ionic/vue'

import { callOutline, call, chatbubble, share, compass, checkmarkCircle, timeOutline, alertCircleOutline } from 'ionicons/icons'
import { useRouter } from 'vue-router'
import { computed } from 'vue'
import { useAuthStore } from '@/stores/userStore'

const authStore = useAuthStore()
const { client } = useApolloClient()

export interface Job {
  description: string;
  expiresAt: string;
  id: string;
  title: string;
  postType: string;
  origin: string;
  destination: string;
  price?: number;
  user?: {
    id: string;
    username: string;
    phoneNumber?: string;
    profilePicture?: string;
  };
  contract?: {
    id: string;
    status: string;
    acceptor: {
      id: string;
      username: string;
    };
  }
}


export interface AllJobsQuery {
  availableJobs: Job[];
}


const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return format(date, 'PPP')
}

const router = useRouter()

const CONFIRM_JOB_ACCEPTANCE = gql`
  mutation confirmJobContract($id: ID!, $poster: ID!) {
    confirmJobContract(id: $id, poster: $poster) {
      success
    }
  }
`;

const ACCEPT_JOB_MUTATION = gql`
  mutation acceptJobPost($jobPostId: ID!, $status: String!) {
    acceptJobPost(jobPostId: $jobPostId, status: $status) {
      contract {
        id
        agreedPrice
        jobPost {
          id
          title
        }
        acceptor {
          id
          username
        }
      }
    }
  }
`;

// GraphQL query to fetch jobs
const JOB_QUERY = gql`
  query JOB_QUERY {
    availableJobs {
      description
      expiresAt
      id
      title
      postType
      origin
      destination
      
    }
  }
`;

const JOB_QUERY_AUTHENTICATED = gql`
  query JOB_QUERY_AUTHENTICATED {
    availableJobs {
      description
      expiresAt
      id
      title
      postType
      origin
      destination
      price
      user {
        id
        username
        phoneNumber
        profilePicture
      }
      contract {
        id
        status
        acceptor {
          id
          username
        }
      }
    }
  }
`;

const handleJobConfirmation = async (contractId: string, posterId: string) => {
  try {
    const result = await client.mutate({
      mutation: CONFIRM_JOB_ACCEPTANCE,
      variables: {
        id: contractId,
        poster: posterId
      }
    });
    console.log('Job confirmed:', result);
    const toast = await toastController.create({ message: 'Job Confirmed successfully!', duration: 2000, color: 'success' });
    await toast.present();
    router.replace('/home');
  } catch (error) {
    console.error('Error confirming job:', error);
    const message = error instanceof Error ? error.message : String(error);
    const toast = await toastController.create({ message, duration: 3000, color: 'danger' });
    await toast.present();
  }
};

const handleAcceptJob = async (jobId: string, status: string) => {
  try {
    const result = await client.mutate({
      mutation: ACCEPT_JOB_MUTATION,
      variables: {
        jobPostId: jobId,
        status: "PENDING"
      }
    });
    console.log('Job accepted:', result);
    const toast = await toastController.create({ message: 'Job Accepted successfully! Waiting for Confimarion from owner', duration: 2000, color: 'success' });
    await toast.present();
    router.replace('/home');
  } catch (error) {
    console.error('Error accepting job:', error);
    const message = error instanceof Error ? error.message : String(error);
    const toast = await toastController.create({ message, duration: 3000, color: 'danger' });
    await toast.present();
  }
};


const currentQuery = computed(() => {
  return localStorage.getItem('authToken') 
    ? JOB_QUERY_AUTHENTICATED 
    : JOB_QUERY;
});


const doRefresh = (event: RefresherCustomEvent) => {
  console.log('Begin async operation...');

  fetchDataFromServer()
    .then(() => {
      console.log('Async operation has ended');
    })
    .catch((err) => {
      console.error('Fetch failed', err);
    })
    .finally(() => {
      event.target.complete(); 
    });
};

const fetchDataFromServer = async () => {
  return new Promise((resolve) => setTimeout(resolve, 2000));
};


const { result, loading, error } = useQuery<AllJobsQuery>(currentQuery);
console.log('Query Data:', result);



</script>

<style scoped>
.hero {
  text-align: center;
  padding-top: 2rem;
  padding-bottom: 1rem;
}
.title {
  font-size: 1.8rem;
  font-weight: 700;
}
.subtitle {
  font-size: 1rem;
  color: var(--ion-color-medium);
}

.fbutton {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  padding-bottom: 30px;
}
.user-info-item {
  --padding-start: 16px;
  --inner-padding-end: 16px;
  background: rgba(var(--ion-color-step-50-rgb), 0.1);
  margin-top: 8px;
}

.user-info-item ion-avatar {
  width: 32px;
  height: 32px;
}
.job-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.full-width-badge {
  width: 100%;
  padding: 10px;
  font-size: 0.9rem;
  --background: var(--ion-color-step-100);
}

/* Ensure the button doesn't hug the edges too tightly */
.ion-padding-horizontal {
  padding-left: 16px;
  padding-right: 16px;
}

ion-card {
  transition: transform 0.2s ease;
}
ion-card:hover {
  transform: scale(1.02);
}
ion-card img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}
</style>
