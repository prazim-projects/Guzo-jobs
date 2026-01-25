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
              <p>Status: {{ getJobStatus(job) }}</p>
              <div v-if="getPendingContracts(job).length > 0" class="pending-applications">
                <p><strong>Pending Applications: {{ getPendingContracts(job).length }}</strong></p>
                <div v-for="contract in getPendingContracts(job)" :key="contract.id" class="application-item">
                  <p>{{ contract.acceptor?.username }} applied</p>
                </div>
              </div>
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
              <p><strong>Price:</strong> ETB{{ job.price }}</p>
              <p><strong>Post Type:</strong> {{ job.postType }}</p>
 
              <!-- For acceptors: show that they were accepted -->
              <div v-if="getUserAcceptedContract(job)?.acceptor?.id === authStore.user?.id">
                <p><strong>Posted by:</strong> {{ job.user?.username }}</p>
                <div v-if="getUserAcceptedContract(job)?.status === 'ACCEPTED'">
                  <p><strong>Status:</strong> Job in progress</p>
                  
                  <!-- Show poster's phone number for acceptors -->
                  <div v-if="job.user?.phoneNumber" class="phone-section">
                    <p><ion-icon name="call-outline"></ion-icon> {{ job.user.phoneNumber }}</p>
                    <ion-button fill="clear" :href="'tel:' + job.user.phoneNumber">
                      <ion-icon slot="icon-only" name="call"></ion-icon>
                    </ion-button>
                  </div>

                  <ion-button expand="block" color="success" @click="completeJob(getUserAcceptedContract(job)?.id!)">
                    Mark as Completed
                  </ion-button>
                </div>
                <div v-else-if="getUserAcceptedContract(job)?.status === 'COMPLETED_BY_ACCEPTOR'">
                  <p><strong>Status:</strong> Waiting for {{ job.user?.username }} to confirm completion</p>
                  <ion-badge color="warning" expand="block">Pending Confirmation</ion-badge>
                </div>
                <div v-else-if="getUserAcceptedContract(job)?.status === 'COMPLETED_BY_POSTER'">
                  <p><strong>Status:</strong> {{ job.user?.username }} marked as completed - please confirm</p>
                  <ion-button expand="block" color="success" @click="completeJob(getUserAcceptedContract(job)?.id!)">
                    Confirm Completion
                  </ion-button>
                </div>
              </div>
              
              <!-- For posters: show who accepted -->
              <div v-else-if="job.user?.id === authStore.user?.id">
                <p><strong>Accepted by:</strong> {{ getUserAcceptedContract(job)?.acceptor?.username }}</p>
                <div v-if="getUserAcceptedContract(job)?.status === 'ACCEPTED'">
                  <p><strong>Status:</strong> Job in progress - waiting for {{ getUserAcceptedContract(job)?.acceptor?.username }} to complete</p>
                  
                  <!-- Show acceptor's phone number for posters -->
                  <div v-if="getUserAcceptedContract(job)?.acceptor?.phoneNumber" class="phone-section">
                    <p><ion-icon name="call-outline"></ion-icon> {{ getUserAcceptedContract(job)?.acceptor?.phoneNumber }}</p>
                    <ion-button fill="clear" :href="'tel:' + getUserAcceptedContract(job)?.acceptor?.phoneNumber">
                      <ion-icon slot="icon-only" name="call"></ion-icon>
                    </ion-button>
                  </div>

                  <ion-button expand="block" color="success" @click="completeJob(getUserAcceptedContract(job)?.id!)">
                    Mark as Completed
                  </ion-button>
                </div>
                <div v-else-if="getUserAcceptedContract(job)?.status === 'COMPLETED_BY_ACCEPTOR'">
                  <p><strong>Status:</strong> {{ getUserAcceptedContract(job)?.acceptor?.username }} marked as completed</p>
                  <ion-button expand="block" color="success" @click="completeJob(getUserAcceptedContract(job)?.id!)">
                    Confirm Completion
                  </ion-button>
                </div>
                <div v-else-if="getUserAcceptedContract(job)?.status === 'COMPLETED_BY_POSTER'">
                  <p><strong>Status:</strong> Waiting for {{ getUserAcceptedContract(job)?.acceptor?.username }} to confirm completion</p>
                  <ion-badge color="warning" expand="block">Pending Confirmation</ion-badge>
                </div>
              </div>
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
              <p><strong>Price:</strong> ${{ job.price }}</p>
              <p><strong>Post Type:</strong> {{ job.postType }}</p>
              
              <!-- For acceptors: show completion status -->
              <div v-if="getUserCompletedContract(job)?.acceptor?.id === authStore.user?.id">
                <p><strong>Status:</strong> Job completed</p>
                <p><strong>Posted by:</strong> {{ job.user?.username }}</p>
              </div>
              
              <!-- For posters: show who completed -->
              <div v-else-if="job.user?.id === authStore.user?.id">
                <p><strong>Completed with:</strong> {{ getUserCompletedContract(job)?.acceptor?.username }}</p>
              </div>
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
              <p><strong>Price:</strong> ${{ job.price }}</p>
              <p><strong>Post Type:</strong> {{ job.postType }}</p>
              <p><strong>Posted by:</strong> {{ job.user?.username }}</p>
            

              <!-- For acceptors: show their pending application -->
              <div v-if="getUserPendingContract(job)">
                <p><strong>Status:</strong> Waiting for confirmation from {{ job.user?.username }}</p>
                <ion-button fill="outline" color="medium" @click="rejectJob(getUserPendingContract(job)?.id!)">Cancel Application</ion-button>
              </div>
              
              <!-- For posters: show all pending applications -->
              <div v-else-if="job.user?.id === authStore.user?.id">
                <h4>Pending Applications:</h4>
                <div v-for="contract in getPendingContracts(job)" :key="contract.id" class="pending-application">
                  <p><strong>Applicant:</strong> {{ contract.acceptor?.username }}</p>
                  <div class="pending-actions">
                    <ion-button size="small" color="success" @click="confirmJob(contract.id)">Accept</ion-button>
                    <ion-button size="small" color="danger" @click="rejectJob(contract.id)">Reject</ion-button>
                  </div>
                </div>
              </div>
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
  IonIcon,
  IonBadge,
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
  price: number;
  postType: string;
  user?: {
    id: string;
    username: string;
    phoneNumber: string;
  };
  contracts?: {
    id: string;
    status: string;
    acceptor?: {
      id: string;
      username: string;
      phoneNumber: string;
    };
  }[];
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
      price
      postType
      user {
        id
        username
        phoneNumber
      }
      contracts {
        id
        status
        acceptor {
          id
          username
          phoneNumber
        }
      }
    }
  }
`;

const COMPLETE_JOB_MUTATION = gql`
  mutation confirmJobCompleted($contractId: ID!) {
    confirmJobCompleted(contractId: $contractId) {
      success
    }
  }
`;

const CONFIRM_JOB_MUTATION = gql`
  mutation confirmJobContract($contractId: ID!) {
    confirmJobContract(contractId: $contractId) {
      success
    }
  }
`;

const REJECT_JOB_MUTATION = gql`
  mutation rejectJobApplication($contractId: ID!) {
    rejectJobApplication(contractId: $contractId) {
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
    job.contracts?.some(contract => 
      (contract.acceptor?.id === authStore.user?.id && (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR')) ||
      (job.user?.id === authStore.user?.id && (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR'))
    )
  );
});

const pendingJobs = computed(() => {
  if (!result.value?.allJobs) return [];
  return result.value.allJobs.filter(job => 
    job.contracts?.some(contract => 
      (contract.acceptor?.id === authStore.user?.id && contract.status === 'PENDING') ||
      (job.user?.id === authStore.user?.id && contract.status === 'PENDING')
    )
  );
});

const completedJobs = computed(() => {
  if (!result.value?.allJobs) return [];
  return result.value.allJobs.filter(job => 
    job.contracts?.some(contract => 
      (contract.acceptor?.id === authStore.user?.id && contract.status === 'COMPLETED') ||
      (job.user?.id === authStore.user?.id && contract.status === 'COMPLETED')
    )
  );
});

const completeJob = async (contractId: string) => {
  try {
    const result = await client.mutate({
      mutation: COMPLETE_JOB_MUTATION,
      variables: {
        contractId: contractId
      }
    });
    console.log('Job completed:', result);
    await refetch(); // Refresh the data
  } catch (error) {
    console.error('Error completing job:', error);
  }
};

const confirmJob = async (contractId: string) => {
  try {
    const result = await client.mutate({
      mutation: CONFIRM_JOB_MUTATION,
      variables: {
        contractId: contractId
      }
    });
    console.log('Job confirmed:', result);
    await refetch();
  } catch (error) {
    console.error('Error confirming job:', error);
  }
};

const rejectJob = async (contractId: string) => {
  try {
    const result = await client.mutate({
      mutation: REJECT_JOB_MUTATION,
      variables: {
        contractId: contractId
      }
    });
    console.log('Job rejected:', result);
    await refetch();
  } catch (error) {
    console.error('Error rejecting job:', error);
  }
};

const getUserContract = (job: Job) => {
  // For acceptors: return their pending contract
  if (job.contracts) {
    const userContract = job.contracts.find(contract => 
      contract.acceptor?.id === authStore.user?.id && contract.status === 'PENDING'
    );
    if (userContract) return userContract;
    
    // For posters: return the first pending contract (they see all pending applications)
    return job.contracts.find(contract => contract.status === 'PENDING');
  }
  return null;
};

const getUserPendingContract = (job: Job) => {
  // Return the user's own pending contract (for acceptors)
  return job.contracts?.find(contract => 
    contract.acceptor?.id === authStore.user?.id && contract.status === 'PENDING'
  );
};

const getUserAcceptedContract = (job: Job) => {
  // Find the contract where the current user is the acceptor
  const acceptorContract = job.contracts?.find(contract => 
    contract.acceptor?.id === authStore.user?.id && 
    (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR')
  );
  if (acceptorContract) return acceptorContract;
  
  // Find the contract where the current user is the poster
  return job.contracts?.find(contract => 
    job.user?.id === authStore.user?.id && 
    (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR')
  );
};

const getUserCompletedContract = (job: Job) => {
  // Find the contract where the current user is the acceptor
  const acceptorContract = job.contracts?.find(contract => 
    contract.acceptor?.id === authStore.user?.id && contract.status === 'COMPLETED'
  );
  if (acceptorContract) return acceptorContract;
  
  // Find the contract where the current user is the poster
  return job.contracts?.find(contract => 
    job.user?.id === authStore.user?.id && contract.status === 'COMPLETED'
  );
};

const getPendingContracts = (job: Job) => {
  return job.contracts?.filter(contract => contract.status === 'PENDING') || [];
};

const getJobStatus = (job: Job) => {
  if (!job.contracts || job.contracts.length === 0) return 'No applications';
  
  const accepted = job.contracts.some(c => c.status === 'ACCEPTED');
  const completedByAcceptor = job.contracts.some(c => c.status === 'COMPLETED_BY_ACCEPTOR');
  const pending = job.contracts.some(c => c.status === 'PENDING');
  const completed = job.contracts.some(c => c.status === 'COMPLETED');
  
  if (completed) return 'Completed';
  if (completedByAcceptor) return 'Pending Completion Confirmation';
  if (accepted) return 'Accepted';
  if (pending) return `Pending (${job.contracts.filter(c => c.status === 'PENDING').length} applications)`;
  return 'Available';
};
</script>

<style scoped>
ion-card {
  margin: 10px;
}

.pending-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.pending-applications {
  margin-top: 8px;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.application-item {
  padding: 4px 0;
  border-bottom: 1px solid #eee;
}

.application-item:last-child {
  border-bottom: none;
}

.phone-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 8px 0;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.phone-section p {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
