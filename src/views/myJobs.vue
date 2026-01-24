<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>My Jobs</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content>
      <ion-segment value="posted" @ionChange="segmentChanged($event)">
        <ion-segment-button value="posted">
          <ion-label>Posted</ion-label>
        </ion-segment-button>
        <ion-segment-button value="accepted">
          <ion-label>Accepted</ion-label>
        </ion-segment-button>
        <ion-segment-button value="completed">
          <ion-label>Completed</ion-label>
        </ion-segment-button>
        <ion-segment-button value="pending">
          <ion-label>Pending</ion-label>
        </ion-segment-button>
      </ion-segment>

      <div v-if="selectedSegment === 'posted'">
        <div v-if="!loading && !error && postedJobs.length">
          <ion-card v-for="job in postedJobs" :key="job.id">
            <ion-card-header>
              <ion-card-title>{{ job.title }}</ion-card-title>
              <ion-card-subtitle>{{ job.origin }} to {{ job.destination }}</ion-card-subtitle>
            </ion-card-header>
            <ion-card-content>
              <p>{{ job.description }}</p>
              <p>Status: {{ job.contract ? job.contract.status : 'No contract' }}</p>
            </ion-card-content>
          </ion-card>
        </div>
        <ion-text v-else-if="!loading">No posted jobs yet.</ion-text>
      </div>

      <div v-if="selectedSegment === 'accepted'">
        <div v-if="!loading && !error && acceptedJobs.length">
          <ion-card v-for="job in acceptedJobs" :key="job.id">
            <ion-card-header>
              <ion-card-title>{{ job.title }}</ion-card-title>
              <ion-card-subtitle>{{ job.origin }} to {{ job.destination }}</ion-card-subtitle>
            </ion-card-header>
            <ion-card-content>
              <p>{{ job.description }}</p>
              <p>Accepted by: {{ job.contract?.acceptor?.username }}</p>
              <ion-button expand="block" color="success" @click="completeJob(job.id)">
                Mark as Completed
              </ion-button>
            </ion-card-content>
          </ion-card>
        </div>
        <ion-text v-else-if="!loading">No accepted jobs yet.</ion-text>
      </div>

      <div v-if="selectedSegment === 'completed'">
        <div v-if="!loading && !error && completedJobs.length">
          <ion-card v-for="job in completedJobs" :key="job.id">
            <ion-card-header>
              <ion-card-title>{{ job.title }}</ion-card-title>
              <ion-card-subtitle>{{ job.origin }} to {{ job.destination }}</ion-card-subtitle>
            </ion-card-header>
            <ion-card-content>
              <p>{{ job.description }}</p>
              <p>Completed</p>
            </ion-card-content>
          </ion-card>
        </div>
        <ion-text v-else-if="!loading">No completed jobs yet.</ion-text>
      </div>

      <div v-if="selectedSegment === 'pending'">
        <div v-if="!loading && !error && pendingJobs.length">
          <ion-card v-for="job in pendingJobs" :key="job.id">
            <ion-card-header>
              <ion-card-title>{{ job.title }}</ion-card-title>
              <ion-card-subtitle>{{ job.origin }} to {{ job.destination }}</ion-card-subtitle>
            </ion-card-header>
            <ion-card-content>
              <p>{{ job.description }}</p>
              <p>Waiting for confirmation from {{ job.user?.username }}</p>
            </ion-card-content>
          </ion-card>
        </div>
        <ion-text v-else-if="!loading">No pending jobs.</ion-text>
      </div>

      <ion-text v-if="loading" class="ion-padding ion-text-center">Loading...</ion-text>
      <ion-text v-if="error" color="danger" class="ion-padding">Error: {{ error.message }}</ion-text>
    </ion-content>
  </ion-page>
</template>

<script lang="ts" setup>
import { gql } from '@apollo/client/core'
import { useQuery } from '@vue/apollo-composable'
import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores/userStore'
import { useApolloClient } from '@vue/apollo-composable'
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonSegment,
  IonSegmentButton,
  IonLabel,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonButton,
  IonText
} from '@ionic/vue'

const authStore = useAuthStore()
const { client } = useApolloClient()
const selectedSegment = ref('posted')

const segmentChanged = (event: any) => {
  selectedSegment.value = event.detail.value
}

interface Job {
  id: string;
  title: string;
  description: string;
  origin: string;
  destination: string;
  user?: {
    id: string;
    username: string;
  };
  contract?: {
    status: string;
    acceptor?: {
      id: string;
      username: string;
    };
  };
}

interface AllJobsQuery {
  allJobs: Job[];
}

const JOB_QUERY_AUTHENTICATED = gql`
  query JOB_QUERY_AUTHENTICATED {
    allJobs {
      id
      title
      description
      origin
      destination
      user {
        id
        username
      }
      contract {
        status
        acceptor {
          id
          username
        }
      }
    }
  }
`;

const COMPLETE_JOB_MUTATION = gql`
  mutation confirmJobCompleted($id: ID!) {
    confirmJobCompleted(id: $id) {
      success
    }
  }
`;

const { result, loading, error, refetch } = useQuery<AllJobsQuery>(JOB_QUERY_AUTHENTICATED);

const postedJobs = computed(() => {
  if (!result.value?.allJobs) return [];
  return result.value.allJobs.filter(job => job.user?.id === authStore.user?.id);
});

const acceptedJobs = computed(() => {
  if (!result.value?.allJobs) return [];
  return result.value.allJobs.filter(job => 
    job.contract?.acceptor?.id === authStore.user?.id && 
    job.contract.status === 'ACCEPTED'
  );
});

const pendingJobs = computed(() => {
  if (!result.value?.allJobs) return [];
  return result.value.allJobs.filter(job => 
    job.contract?.acceptor?.id === authStore.user?.id && 
    job.contract.status === 'PENDING'
  );
});

const completedJobs = computed(() => {
  if (!result.value?.allJobs) return [];
  return result.value.allJobs.filter(job => 
    job.contract?.acceptor?.id === authStore.user?.id && 
    job.contract.status === 'COMPLETED'
  );
});

const completeJob = async (jobId: string) => {
  try {
    const result = await client.mutate({
      mutation: COMPLETE_JOB_MUTATION,
      variables: {
        id: jobId
      }
    });
    console.log('Job completed:', result);
    await refetch(); // Refresh the data
  } catch (error) {
    console.error('Error completing job:', error);
  }
};
</script>

<style scoped>
ion-card {
  margin: 10px;
}
</style>
