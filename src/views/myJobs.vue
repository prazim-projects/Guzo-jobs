<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>My Jobs</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content>
      <ion-refresher slot="fixed" @ionRefresh="doRefresh($event)">
        <ion-refresher-content pulling-text="Pull to refresh" refreshing-spinner="circles" refreshing-text="Updating data..."></ion-refresher-content>
      </ion-refresher>
      <ion-segment :value="selectedSegment" @ionChange="segmentChanged($event)">
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
              <ion-button expand="block" color="danger" fill="outline" @click="deleteJob(job.id)">
                Delete Post
              </ion-button>
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
                  <p v-if="!hasPaidEscrow(getUserAcceptedContract(job))"><strong>Status:</strong> Waiting for poster escrow deposit via Telebirr</p>
                  <p v-else><strong>Status:</strong> Escrow funded, job in progress</p>
                  <ion-button v-if="hasPaidEscrow(getUserAcceptedContract(job))" expand="block" color="success" @click="completeJob(getUserAcceptedContract(job)?.id!)">
                    Mark as Completed
                  </ion-button>
                  <ion-button expand="block" color="warning" fill="outline" @click="openComplaint(getUserAcceptedContract(job)?.id!)">
                    Raise Complaint
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
                  <p v-if="!hasPaidEscrow(getUserAcceptedContract(job))"><strong>Status:</strong> Deposit full amount to escrow before work starts</p>
                  <p v-else><strong>Status:</strong> Escrow funded. Waiting for {{ getUserAcceptedContract(job)?.acceptor?.username }} to complete</p>
                  <div v-if="!hasPaidEscrow(getUserAcceptedContract(job))" class="escrow-guide">
                    <p><strong>Escrow Steps</strong></p>
                    <p>1. Send <strong>ETB{{ job.price }}</strong> via Telebirr to:</p>
                    <p><strong>{{ platformTelebirrReceiverName }}</strong> ({{ platformTelebirrPhone }})</p>
                    <p>2. Copy your Telebirr receipt link.</p>
                    <p>3. Paste the link below and tap verify.</p>
                    <div class="guide-actions">
                      <ion-button size="small" fill="outline" @click="copyReceiverPhone">
                        Copy Phone
                      </ion-button>
                      <ion-button size="small" fill="outline" :href="TELEBIRR_RECEIPT_PREFIX" target="_blank" rel="noopener noreferrer">
                        Open Receipt Portal
                      </ion-button>
                    </div>
                  </div>
                  <ion-item v-if="!hasPaidEscrow(getUserAcceptedContract(job))" lines="none">
                    <ion-label position="stacked">Telebirr Receipt Link</ion-label>
                    <ion-input
                      v-model="receiptLinks[getUserAcceptedContract(job)?.id || '']"
                      placeholder="https://transactioninfo.ethiotelecom.et/receipt/DDJ..."
                    ></ion-input>
                  </ion-item>
                  <ion-button
                    v-if="!hasPaidEscrow(getUserAcceptedContract(job))"
                    expand="block"
                    color="secondary"
                    @click="fundEscrow(getUserAcceptedContract(job)?.id!)"
                  >
                    Verify Telebirr Receipt and Fund Escrow
                  </ion-button>
                  <ion-button v-if="hasPaidEscrow(getUserAcceptedContract(job))" expand="block" color="success" @click="completeJob(getUserAcceptedContract(job)?.id!)">
                    Mark as Completed
                  </ion-button>
                  <ion-button expand="block" color="warning" fill="outline" @click="openComplaint(getUserAcceptedContract(job)?.id!)">
                    Raise Complaint
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
                  <div class="acceptance-pulse" aria-hidden="true"></div>
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
import { isCurrentUserId } from '@/utils/jobHelpers'
import { t } from '@/utils/i18n'
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonRefresher,
  IonRefresherContent,
  IonSegment,
  IonSegmentButton,
  IonLabel,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonItem,
  IonInput,
  IonButton,
  IonBadge,
  IonText,
  RefresherCustomEvent,
  toastController
} from '@ionic/vue'

const authStore = useAuthStore()
const { client } = useApolloClient()
const selectedSegment = ref('posted')
const receiptLinks = ref<Record<string, string>>({})
const platformTelebirrPhone = import.meta.env.VITE_PLATFORM_TELEBIRR_PHONE || '+2519XXXXXXXX'
const platformTelebirrReceiverName = import.meta.env.VITE_PLATFORM_TELEBIRR_RECEIVER_NAME || 'Bealprasim Demere Tefera'
const TELEBIRR_RECEIPT_PREFIX = 'https://transactioninfo.ethiotelecom.et/receipt/'

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
  };
  contracts?: {
    id: string;
    status: string;
    acceptor?: {
      id: string;
      username: string;
    };
  }[];
    preferredPaymentMethod?: string;
    escrowPayments?: {
      id: string;
      status: string;
      paymentMethod: string;
      amount: number;
    }[];
}

interface AllJobsQuery {
  myJobs: Job[];
}

const JOB_QUERY_AUTHENTICATED = gql`
  query JOB_QUERY_AUTHENTICATED {
    myJobs {
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
      }
      contracts {
        id
        status
        preferredPaymentMethod
        escrowPayments {
          id
          status
          paymentMethod
          amount
        }
        acceptor {
          id
          username
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

const DELETE_JOB_MUTATION = gql`
  mutation deleteJobPost($jobPostId: ID!) {
    deleteJobPost(jobPostId: $jobPostId) {
      success
    }
  }
`;

const INITIATE_ESCROW_MUTATION = gql`
  mutation InitiateEscrowPayment($contractId: ID!, $receiptUrl: String!) {
    initiateEscrowPayment(contractId: $contractId, receiptUrl: $receiptUrl) {
      verified
      message
      payment {
        id
        status
        paymentMethod
        receiptUrl
        verificationNote
      }
    }
  }
`;

const CREATE_COMPLAINT_MUTATION = gql`
  mutation CreateComplaint($contractId: ID!, $reason: String!) {
    createComplaint(contractId: $contractId, reason: $reason) {
      complaint {
        id
      }
    }
  }
`;

const { result, loading, error, refetch } = useQuery<AllJobsQuery>(JOB_QUERY_AUTHENTICATED, null, {
  fetchPolicy: 'cache-first',
  pollInterval: 180000,
});

const hardRefreshData = async () => {
  await refetch();
};

const doRefresh = async (event: RefresherCustomEvent) => {
  try {
    await hardRefreshData();
    const toast = await toastController.create({
      message: `${t('refresh_done')} ${t('refresh_notice')}`,
      duration: 2200,
      color: 'success',
      position: 'bottom',
      positionAnchor: 'main-tab-bar',
    });
    await toast.present();
  } finally {
    event.target.complete();
  }
};

const postedJobs = computed(() => {
  if (!result.value?.myJobs) return [];
  return result.value.myJobs.filter(job => isCurrentUserId(job.user?.id, authStore.user?.id));
});

const acceptedJobs = computed(() => {
  if (!result.value?.myJobs) return [];
  return result.value.myJobs.filter(job => 
    job.contracts?.some(contract => 
      (isCurrentUserId(contract.acceptor?.id, authStore.user?.id) && (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR')) ||
      (isCurrentUserId(job.user?.id, authStore.user?.id) && (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR'))
    )
  );
});

const pendingJobs = computed(() => {
  if (!result.value?.myJobs) return [];
  return result.value.myJobs.filter(job => 
    job.contracts?.some(contract => 
      (isCurrentUserId(contract.acceptor?.id, authStore.user?.id) && contract.status === 'PENDING') ||
      (isCurrentUserId(job.user?.id, authStore.user?.id) && contract.status === 'PENDING')
    )
  );
});

const completedJobs = computed(() => {
  if (!result.value?.myJobs) return [];
  return result.value.myJobs.filter(job => 
    job.contracts?.some(contract => 
      (isCurrentUserId(contract.acceptor?.id, authStore.user?.id) && contract.status === 'COMPLETED') ||
      (isCurrentUserId(job.user?.id, authStore.user?.id) && contract.status === 'COMPLETED')
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
    await hardRefreshData();
  } catch (error) {
    console.error('Error completing job:', error);
  }
};

const confirmJob = async (contractId: string) => {
  const jobForContract = result.value?.myJobs.find(job => job.contracts?.some(contract => contract.id === contractId));
  if (!isCurrentUserId(jobForContract?.user?.id, authStore.user?.id)) {
    console.warn('Blocked confirmation attempt by non-owner user.');
    return;
  }

  try {
    const result = await client.mutate({
      mutation: CONFIRM_JOB_MUTATION,
      variables: {
        contractId: contractId
      }
    });
    console.log('Job confirmed:', result);
    await hardRefreshData();
    selectedSegment.value = 'accepted';
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
    await hardRefreshData();
  } catch (error) {
    console.error('Error rejecting job:', error);
  }
};

const deleteJob = async (jobId: string) => {
  try {
    await client.mutate({
      mutation: DELETE_JOB_MUTATION,
      variables: {
        jobPostId: jobId,
      },
    });
    await hardRefreshData();
  } catch (error) {
    console.error('Error deleting job:', error);
  }
};

const fundEscrow = async (contractId: string) => {
  const receiptUrl = (receiptLinks.value[contractId] || '').trim();
  if (!receiptUrl) {
    const toast = await toastController.create({ message: 'Receipt URL is required.', duration: 2200, color: 'warning' });
    await toast.present();
    return;
  }

  if (!receiptUrl.startsWith(TELEBIRR_RECEIPT_PREFIX)) {
    const toast = await toastController.create({
      message: `Use a valid Telebirr receipt link starting with ${TELEBIRR_RECEIPT_PREFIX}`,
      duration: 3200,
      color: 'warning',
      position: 'bottom',
      positionAnchor: 'main-tab-bar',
    });
    await toast.present();
    return;
  }

  try {
    const response = await client.mutate({
      mutation: INITIATE_ESCROW_MUTATION,
      variables: {
        contractId,
        receiptUrl,
      }
    });

    const payload = response.data?.initiateEscrowPayment;
    const toast = await toastController.create({
      message: `${payload?.message || 'Verification submitted.'} ${t('refresh_notice')}`,
      duration: 3000,
      color: payload?.verified ? 'success' : 'warning',
      position: 'bottom',
      positionAnchor: 'main-tab-bar',
    });
    await toast.present();
    await hardRefreshData();
  } catch (error) {
    console.error('Error funding escrow:', error);
    const message = error instanceof Error ? error.message : String(error);
    const toast = await toastController.create({ message, duration: 3000, color: 'danger' });
    await toast.present();
  }
};

const copyReceiverPhone = async () => {
  try {
    await navigator.clipboard.writeText(platformTelebirrPhone);
    const toast = await toastController.create({
      message: `Receiver phone copied: ${platformTelebirrPhone}`,
      duration: 2000,
      color: 'success',
      position: 'bottom',
      positionAnchor: 'main-tab-bar',
    });
    await toast.present();
  } catch {
    const toast = await toastController.create({
      message: `Receiver phone: ${platformTelebirrPhone}`,
      duration: 2500,
      color: 'medium',
      position: 'bottom',
      positionAnchor: 'main-tab-bar',
    });
    await toast.present();
  }
};

const openComplaint = async (contractId: string) => {
  try {
    await client.mutate({
      mutation: CREATE_COMPLAINT_MUTATION,
      variables: {
        contractId,
        reason: 'Issue reported from mobile app. Please review this contract.'
      }
    });
    await hardRefreshData();
  } catch (error) {
    console.error('Error creating complaint:', error);
  }
};

const hasPaidEscrow = (_contract?: unknown) => true;


const getUserPendingContract = (job: Job) => {
  // Return the user's own pending contract (for acceptors)
  return job.contracts?.find(contract => 
    isCurrentUserId(contract.acceptor?.id, authStore.user?.id) && contract.status === 'PENDING'
  );
};

const getUserAcceptedContract = (job: Job) => {
  // Find the contract where the current user is the acceptor
  const acceptorContract = job.contracts?.find(contract => 
    isCurrentUserId(contract.acceptor?.id, authStore.user?.id) && 
    (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR')
  );
  if (acceptorContract) return acceptorContract;
  
  // Find the contract where the current user is the poster
  return job.contracts?.find(contract => 
    isCurrentUserId(job.user?.id, authStore.user?.id) && 
    (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR')
  );
};

const getUserCompletedContract = (job: Job) => {
  // Find the contract where the current user is the acceptor
  const acceptorContract = job.contracts?.find(contract => 
    isCurrentUserId(contract.acceptor?.id, authStore.user?.id) && contract.status === 'COMPLETED'
  );
  if (acceptorContract) return acceptorContract;
  
  // Find the contract where the current user is the poster
  return job.contracts?.find(contract => 
    isCurrentUserId(job.user?.id, authStore.user?.id) && contract.status === 'COMPLETED'
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

.acceptance-pulse {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--ion-color-warning);
  margin: 6px 0;
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.35; }
  100% { transform: scale(0.95); opacity: 1; }
}
</style>
