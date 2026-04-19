<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/profile"></ion-back-button>
        </ion-buttons>
        <ion-title>Support</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <ion-refresher slot="fixed" @ionRefresh="doRefresh($event)">
        <ion-refresher-content pulling-text="Pull to refresh" refreshing-spinner="circles" refreshing-text="Updating data..."></ion-refresher-content>
      </ion-refresher>
      <ion-item>
        <ion-label position="stacked">Related Job (optional)</ion-label>
        <ion-select v-model="selectedContractId" interface="action-sheet" placeholder="Choose a job contract">
          <ion-select-option v-for="contract in availableContracts" :key="contract.id" :value="contract.id">
            {{ contract.jobPost.title }} - {{ contract.status }}
          </ion-select-option>
        </ion-select>
      </ion-item>

      <ion-item>
        <ion-label position="stacked">Subject</ion-label>
        <ion-input v-model="subject" placeholder="What do you need help with?"></ion-input>
      </ion-item>

      <ion-item>
        <ion-label position="stacked">Message</ion-label>
        <ion-textarea v-model="message" :rows="5" auto-grow placeholder="Describe the issue..."></ion-textarea>
      </ion-item>

      <ion-button expand="block" class="ion-margin-top" @click="submitTicket" :disabled="!subject || !message || submitting">
        Submit Ticket
      </ion-button>

      <ion-list class="ion-margin-top" v-if="tickets.length">
        <ion-list-header>
          <ion-label>Your Tickets</ion-label>
        </ion-list-header>
        <ion-item v-for="ticket in tickets" :key="ticket.id" lines="full">
          <ion-label>
            <h2>{{ ticket.subject }}</h2>
            <p>{{ ticket.message }}</p>
            <p v-if="ticket.contract">Job: {{ ticket.contract.jobPost.title }}</p>
            <p>Status: {{ ticket.status }}</p>
          </ion-label>
        </ion-item>
      </ion-list>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { gql } from '@apollo/client/core';
import { useApolloClient, useQuery } from '@vue/apollo-composable';
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonBackButton,
  IonContent,
  IonRefresher,
  IonRefresherContent,
  IonItem,
  IonLabel,
  IonInput,
  IonSelect,
  IonSelectOption,
  IonTextarea,
  IonButton,
  IonList,
  IonListHeader,
  RefresherCustomEvent,
  toastController,
} from '@ionic/vue';
import { t } from '@/utils/i18n';

const { client } = useApolloClient();
const subject = ref('');
const message = ref('');
const selectedContractId = ref<string | null>(null);
const submitting = ref(false);

const MY_ACTIVE_CONTRACTS = gql`
  query MyActiveContractsForSupport {
    allJobs {
      id
      title
      user { id }
      contracts {
        id
        status
        acceptor { id }
        jobPost {
          id
          title
        }
      }
    }
  }
`;

const MY_SUPPORT_TICKETS = gql`
  query MySupportTickets {
    mySupportTickets {
      id
      subject
      message
      status
      createdAt
      contract {
        id
        jobPost {
          id
          title
        }
      }
    }
  }
`;

const CREATE_SUPPORT_TICKET = gql`
  mutation CreateSupportTicket($subject: String!, $message: String!, $contractId: ID) {
    createSupportTicket(subject: $subject, message: $message, contractId: $contractId) {
      ticket {
        id
      }
    }
  }
`;

const { result, refetch } = useQuery(MY_SUPPORT_TICKETS);
const { result: activeContractsResult, refetch: refetchActiveContracts } = useQuery(MY_ACTIVE_CONTRACTS, null, {
  fetchPolicy: 'network-only',
  pollInterval: 30000,
});

const tickets = computed(() => result.value?.mySupportTickets || []);
const userId = computed(() => localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user') || '{}')?.id : null);
const availableContracts = computed(() => {
  const jobs = activeContractsResult.value?.allJobs || [];
  const flatContracts = jobs.flatMap((job: any) => job.contracts || []);
  const mine = flatContracts.filter((contract: any) => {
    const isPoster = String(jobOwnerIdForContract(jobs, contract.id)) === String(userId.value || '');
    const isAcceptor = String(contract.acceptor?.id || '') === String(userId.value || '');
    return isPoster || isAcceptor;
  });

  const linkedTicketContractIds = new Set((tickets.value || []).map((ticket: any) => ticket.contract?.id).filter(Boolean));
  return mine.filter((contract: any) => !linkedTicketContractIds.has(contract.id));
});

const jobOwnerIdForContract = (jobs: any[], contractId: string) => {
  const job = jobs.find((j: any) => (j.contracts || []).some((contract: any) => contract.id === contractId));
  return job?.user?.id;
};

const submitTicket = async () => {
  submitting.value = true;
  try {
    await client.mutate({
      mutation: CREATE_SUPPORT_TICKET,
      variables: {
        subject: subject.value,
        message: message.value,
        contractId: selectedContractId.value,
      },
    });
    subject.value = '';
    message.value = '';
    selectedContractId.value = null;
    await refetch();
  } finally {
    submitting.value = false;
  }
};

const doRefresh = async (event: RefresherCustomEvent) => {
  try {
    await Promise.all([refetch(), refetchActiveContracts()]);
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
</script>
