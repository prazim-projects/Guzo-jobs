<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>{{ t("My Jobs") }}</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content>
      <ion-refresher slot="fixed" @ionRefresh="doRefresh($event)">
        <ion-refresher-content pulling-text="Pull to refresh" refreshing-spinner="circles" refreshing-text="Updating data..."></ion-refresher-content>
      </ion-refresher>
      <ion-segment :value="selectedSegment" @ionChange="segmentChanged($event)">
        <ion-segment-button value="posted">
          <ion-label>{{ t("Posted") }}</ion-label>
        </ion-segment-button>
        <ion-segment-button value="accepted">
          <ion-label>{{ t("Accepted") }}</ion-label>
        </ion-segment-button>
        <ion-segment-button value="completed">
          <ion-label>{{ t("Completed") }}</ion-label>
        </ion-segment-button>
        <ion-segment-button value="pending">
          <ion-label>{{ t("Pending") }}</ion-label>
        </ion-segment-button>
      </ion-segment>

      <div v-if="selectedSegment === 'posted'">
        <div v-if="!activeLoading && !activeError && postedJobs.length">
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
                {{ t("Delete Post") }}
              </ion-button>
            </ion-card-content>
          </ion-card>
        </div>
        <ion-text v-else-if="!activeLoading">No posted jobs yet.</ion-text>
      </div>

      <div v-if="selectedSegment === 'accepted'">
        <div v-if="!activeLoading && !activeError && acceptedJobs.length">
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
                    {{ t("Mark as Completed") }}
                  </ion-button>
                  <ion-button expand="block" color="warning" fill="outline" @click="openComplaint(getUserAcceptedContract(job)?.id!)">
                    {{ t("Raise Complaint") }}
                  </ion-button>
                </div>
                <div v-else-if="getUserAcceptedContract(job)?.status === 'COMPLETED_BY_ACCEPTOR'">
                  <p><strong>Status:</strong> Waiting for {{ job.user?.username }} to confirm completion</p>
                  <ion-badge color="warning" expand="block">Pending Confirmation</ion-badge>
                </div>
                <div v-else-if="getUserAcceptedContract(job)?.status === 'COMPLETED_BY_POSTER'">
                  <p><strong>Status:</strong> {{ job.user?.username }} marked as completed - please confirm</p>
                  <ion-button expand="block" color="success" @click="completeJob(getUserAcceptedContract(job)?.id!)">
                    {{ t("Confirm Completion") }}
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
                        {{ t("Copy Phone") }}
                      </ion-button>
                      <ion-button size="small" fill="outline" :href="TELEBIRR_RECEIPT_PREFIX" target="_blank" rel="noopener noreferrer">
                        {{ t("Open Receipt Portal") }}
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
                    {{ t("Verify Telebirr Receipt and Fund Escrow") }}
                  </ion-button>
                  <ion-button v-if="hasPaidEscrow(getUserAcceptedContract(job))" expand="block" color="success" @click="completeJob(getUserAcceptedContract(job)?.id!)">
                    {{ t("Mark as Completed") }}
                  </ion-button>
                  <ion-button expand="block" color="warning" fill="outline" @click="openComplaint(getUserAcceptedContract(job)?.id!)">
                    {{ t("Raise Complaint") }}
                  </ion-button>
                </div>
                <div v-else-if="getUserAcceptedContract(job)?.status === 'COMPLETED_BY_ACCEPTOR'">
                  <p><strong>Status:</strong> {{ getUserAcceptedContract(job)?.acceptor?.username }} marked as completed</p>
                  <ion-button expand="block" color="success" @click="completeJob(getUserAcceptedContract(job)?.id!)">
                    {{ t("Confirm Completion") }}
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
        <ion-text v-else-if="!activeLoading">No accepted jobs yet.</ion-text>
      </div>

      <div v-if="selectedSegment === 'completed'">
        <div v-if="!activeLoading && !activeError && completedJobs.length">
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
        <ion-text v-else-if="!activeLoading">No completed jobs yet.</ion-text>
      </div>

      <div v-if="selectedSegment === 'pending'">
        <div v-if="!activeLoading && !activeError && pendingJobs.length">
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
                <ion-button fill="outline" color="medium" @click="rejectJob(getUserPendingContract(job)?.id!)">{{ t("Cancel Application") }}</ion-button>
              </div>
              
              <!-- For posters: show all pending applications -->
              <div v-else-if="job.user?.id === authStore.user?.id">
                <h4>Pending Applications:</h4>
                <div v-for="contract in getPendingContracts(job)" :key="contract.id" class="pending-application">
                  <p><strong>Applicant:</strong> {{ contract.acceptor?.username }}</p>
                  <div class="acceptance-pulse" aria-hidden="true"></div>
                  <div class="pending-actions">
                    <ion-button size="small" color="success" @click="confirmJob(contract.id)">{{ t("Accept") }}</ion-button>
                    <ion-button size="small" color="danger" @click="rejectJob(contract.id)">{{ t("Reject") }}</ion-button>
                  </div>
                </div>
              </div>
            </ion-card-content>
          </ion-card>
        </div>
        <ion-text v-else-if="!activeLoading">No pending jobs.</ion-text>
      </div>

      <ion-text v-if="activeLoading" class="ion-padding ion-text-center">Loading...</ion-text>
      <ion-text v-if="activeError" color="danger" class="ion-padding">Error: {{ activeError.message }}</ion-text>
    </ion-content>
  </ion-page>
</template>

<script lang="ts" setup>
import { gql } from '@apollo/client/core'
import { computed, onMounted, reactive, ref } from 'vue'
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
type JobsSegment = 'posted' | 'accepted' | 'completed' | 'pending'

const selectedSegment = ref<JobsSegment>('posted')
const receiptLinks = ref<Record<string, string>>({})
const platformTelebirrPhone = import.meta.env.VITE_PLATFORM_TELEBIRR_PHONE || '+2519XXXXXXXX'
const platformTelebirrReceiverName = import.meta.env.VITE_PLATFORM_TELEBIRR_RECEIVER_NAME || 'Bealprasim Demere Tefera'
const TELEBIRR_RECEIPT_PREFIX = 'https://transactioninfo.ethiotelecom.et/receipt/'
const SEGMENT_STALE_MS = 60_000
const REFRESH_DEDUPE_MS = 10_000

const segmentChanged = (event: any) => {
  const nextSegment = event.detail.value as JobsSegment
  selectedSegment.value = nextSegment
  void fetchSegment(nextSegment)
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

interface SegmentJobsQuery {
  jobs: Job[];
}

interface SegmentState {
  jobs: Job[];
  loading: boolean;
  error: Error | null;
  lastFetched: number;
}

const JOB_FIELDS = gql`
  fragment MyJobsFields on JobPostingType {
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
`;

const JOB_QUERY_AUTHENTICATED = gql`
  ${JOB_FIELDS}
  query JOB_QUERY_AUTHENTICATED {
    myJobs {
      ...MyJobsFields
    }
  }
`;

const SEGMENT_QUERIES = {
  posted: gql`
    ${JOB_FIELDS}
    query PostedJobsQuery {
      jobs: myJobs {
        ...MyJobsFields
      }
    }
  `,
  accepted: gql`
    ${JOB_FIELDS}
    query AcceptedJobsQuery {
      jobs: myJobs {
        ...MyJobsFields
      }
    }
  `,
  completed: gql`
    ${JOB_FIELDS}
    query CompletedJobsQuery {
      jobs: myJobs {
        ...MyJobsFields
      }
    }
  `,
  pending: gql`
    ${JOB_FIELDS}
    query PendingJobsQuery {
      jobs: myJobs {
        ...MyJobsFields
      }
    }
  `,
} satisfies Record<JobsSegment, ReturnType<typeof gql>>;

const segmentState = reactive<Record<JobsSegment, SegmentState>>({
  posted: { jobs: [], loading: false, error: null, lastFetched: 0 },
  accepted: { jobs: [], loading: false, error: null, lastFetched: 0 },
  completed: { jobs: [], loading: false, error: null, lastFetched: 0 },
  pending: { jobs: [], loading: false, error: null, lastFetched: 0 },
});
const inFlightRequests = new Map<JobsSegment, Promise<void>>();
let allSegmentsRequest: Promise<void> | null = null;
let allSegmentsLastFetched = 0;

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

const getSegmentJobs = (segment: JobsSegment) => segmentState[segment].jobs;

const shouldFetchSegment = (segment: JobsSegment, preferNetwork = false) => {
  const state = segmentState[segment];
  if (state.loading || inFlightRequests.has(segment)) return false;
  if (!state.lastFetched) return true;

  const age = Date.now() - state.lastFetched;
  return preferNetwork ? age > REFRESH_DEDUPE_MS : age > SEGMENT_STALE_MS;
};

const fetchSegment = (segment: JobsSegment, options: { preferNetwork?: boolean } = {}) => {
  if (!shouldFetchSegment(segment, options.preferNetwork)) {
    return inFlightRequests.get(segment) ?? Promise.resolve();
  }

  const state = segmentState[segment];
  state.loading = true;
  state.error = null;

  const request = client.query<SegmentJobsQuery>({
    query: SEGMENT_QUERIES[segment],
    fetchPolicy: options.preferNetwork ? 'network-only' : 'cache-first',
  }).then(({ data }) => {
    state.jobs = data.jobs || [];
    state.lastFetched = Date.now();
  }).catch((error: Error) => {
    state.error = error;
    throw error;
  }).finally(() => {
    state.loading = false;
    inFlightRequests.delete(segment);
  });

  inFlightRequests.set(segment, request);
  return request;
};

const setAllSegmentJobs = (jobs: Job[]) => {
  (Object.keys(segmentState) as JobsSegment[]).forEach(segment => {
    segmentState[segment].jobs = jobs;
    segmentState[segment].lastFetched = Date.now();
    segmentState[segment].error = null;
  });
};

const hardRefreshData = async (options: { force?: boolean } = {}) => {
  const age = Date.now() - allSegmentsLastFetched;
  if (!options.force && allSegmentsLastFetched && age <= REFRESH_DEDUPE_MS) {
    return allSegmentsRequest ?? Promise.resolve();
  }
  if (allSegmentsRequest) return allSegmentsRequest;

  (Object.keys(segmentState) as JobsSegment[]).forEach(segment => {
    segmentState[segment].loading = true;
  });

  allSegmentsRequest = client.query<AllJobsQuery>({
    query: JOB_QUERY_AUTHENTICATED,
    fetchPolicy: 'network-only',
  }).then(({ data }) => {
    setAllSegmentJobs(data.myJobs || []);
    allSegmentsLastFetched = Date.now();
  }).catch((error: Error) => {
    (Object.keys(segmentState) as JobsSegment[]).forEach(segment => {
      segmentState[segment].error = error;
    });
    throw error;
  }).finally(() => {
    (Object.keys(segmentState) as JobsSegment[]).forEach(segment => {
      segmentState[segment].loading = false;
    });
    allSegmentsRequest = null;
  });

  return allSegmentsRequest;
};

const doRefresh = async (event: RefresherCustomEvent) => {
  try {
    await hardRefreshData({ force: true });
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
  return getSegmentJobs('posted').filter(job => isCurrentUserId(job.user?.id, authStore.user?.id));
});

const acceptedJobs = computed(() => {
  return getSegmentJobs('accepted').filter(job => 
    job.contracts?.some(contract => 
      (isCurrentUserId(contract.acceptor?.id, authStore.user?.id) && (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR')) ||
      (isCurrentUserId(job.user?.id, authStore.user?.id) && (contract.status === 'ACCEPTED' || contract.status === 'COMPLETED_BY_ACCEPTOR'))
    )
  );
});

const pendingJobs = computed(() => {
  return getSegmentJobs('pending').filter(job => 
    job.contracts?.some(contract => 
      (isCurrentUserId(contract.acceptor?.id, authStore.user?.id) && contract.status === 'PENDING') ||
      (isCurrentUserId(job.user?.id, authStore.user?.id) && contract.status === 'PENDING')
    )
  );
});

const completedJobs = computed(() => {
  return getSegmentJobs('completed').filter(job => 
    job.contracts?.some(contract => 
      (isCurrentUserId(contract.acceptor?.id, authStore.user?.id) && contract.status === 'COMPLETED') ||
      (isCurrentUserId(job.user?.id, authStore.user?.id) && contract.status === 'COMPLETED')
    )
  );
});

const activeLoading = computed(() => segmentState[selectedSegment.value].loading);
const activeError = computed(() => segmentState[selectedSegment.value].error);

onMounted(() => {
  void fetchSegment(selectedSegment.value);
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
    await hardRefreshData({ force: true });
  } catch (error) {
    console.error('Error completing job:', error);
  }
};

const confirmJob = async (contractId: string) => {
  const allLoadedJobs = Object.values(segmentState).flatMap(state => state.jobs);
  const jobForContract = allLoadedJobs.find(job => job.contracts?.some(contract => contract.id === contractId));
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
    await hardRefreshData({ force: true });
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
    await hardRefreshData({ force: true });
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
    await hardRefreshData({ force: true });
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
    await hardRefreshData({ force: true });
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
