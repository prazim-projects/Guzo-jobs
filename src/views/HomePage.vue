<template>
  <ion-page>
    <ion-content >
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
      <ion-grid v-if="!loading && !error && result?.allJobs?.length">
        <ion-row>
          <ion-col
            size="12"
            size-md="6"
            size-sm="4"
            v-for="job in result.allJobs">
            <ion-card class="job-card">

              <!-- Dynamic Picsum image based on destination -->
              <img
                :src="`https://picsum.photos/seed/${encodeURIComponent(job.destination)}/500/300`"
                alt="Image for trip to {{ job.destination }}"
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

              <ion-card-content class="ion-text-end">
                <ion-buttons>
                  <ion-button
                    v-for="action in actions"
                    :key="action.name"
                    fill="clear"
                    size="small"
                    @click="action.onClick()"
                  >
                    <ion-icon :name="action.icon"></ion-icon>
                  </ion-button>
                </ion-buttons>
              </ion-card-content>

            </ion-card>
            </ion-col>
          </ion-row>
        </ion-grid>
      <ion-text v-if="loading">Loading...</ion-text>
      <ion-text v-if="error">Error: {{ error.message }}</ion-text>
    </ion-content>
    <!-- <floatingPostButton class="fbutton" @on-click="router.push('/add')"/> -->
    
  </ion-page>
</template>

<script lang="ts" setup>
// import floatingPostButton from '@/components/floatingPostButton.vue'
import { gql } from '@apollo/client/core'
import { useApolloClient } from '@vue/apollo-composable'
import { useQuery } from '@vue/apollo-composable'
import { format } from 'date-fns'
import {
  IonPage,
  IonContent,
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
  RefresherCustomEvent
} from '@ionic/vue'

import { useRouter } from 'vue-router'

export interface Job {
  description: string;
  expiresAt: string;
  id: string;
  title: string;
  postType: string;
  origin: string;
  destination: string;
}

export interface AllJobsQuery {
  allJobs: Job[];
}


const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return format(date, 'PPP')
}

const navRoutes = [
  { path: '/', label: 'Home', icon: 'home-outline' },
  { path: '/add', label: 'Add Note', icon: 'add' },
  { path: '/login', label: 'Login', icon: 'log-in-outline' },
  { path: '/profile', label: 'Profile', icon: 'person-circle-outline' },
  { path: '/mapET', label: 'Map ET', icon: 'map-outline' },
  { path: '/signup', label: 'Signup', icon: 'person-add-outline' },
];

const actions = [
   { name: "comment", icon: "chatbubble", onClick: () => console.log("Comment") },
  { name: "share", icon: "share", onClick: () => console.log("Shared!") },
  {name: "route", icon: "compass", onClick: () => console.log("Route!") },
];



const router = useRouter()



// GraphQL query to fetch jobs
const JOB_QUERY = gql`
  query JOB_QUERY {
    allJobs {
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


//  Typed Query Execution
const { result, loading, error } = useQuery<AllJobsQuery>(JOB_QUERY);

// Debug line to check client
const { client } = useApolloClient();
console.log('Apollo Client:', client);
console.log('watchQuery exists?', typeof client?.watchQuery === 'function');

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
