<template>
  <section class="escrow-guide" aria-label="Fund escrow">
    <h3>Fund escrow</h3>
    <p v-if="loading" role="status">Loading receiving accounts…</p>
    <p v-else-if="!recipients.length">Escrow accounts are not configured. Contact support before sending money.</p>
    <template v-else>
      <p>Send exactly <strong>{{ Number(amount).toFixed(2) }} ETB</strong> to one of these accounts. Pay provider fees separately.</p>
      <div v-for="recipient in recipients" :key="recipient.provider" class="recipient">
        <strong>{{ recipient.provider === 'CBE' ? 'Commercial Bank of Ethiopia' : 'Telebirr' }}</strong>
        <p>{{ recipient.name }}<br /><span class="account-number">{{ recipient.accountNumber }}</span></p>
        <ion-button size="small" fill="outline" @click="copyAccount(recipient.accountNumber)">Copy account</ion-button>
      </div>
      <p>After transferring, paste the original receipt link from CBE or Telebirr. Keep your receipt until verification succeeds.</p>
      <form @submit.prevent="verify">
        <ion-input v-model="receiptUrl" label="Receipt link" label-placement="stacked" type="url" inputmode="url" placeholder="https://…" :disabled="busy" required />
        <ion-button type="submit" expand="block" :disabled="busy || !receiptUrl.trim()" @click.prevent="verify">{{ busy ? 'Verifying receipt…' : 'Verify payment' }}</ion-button>
      </form>
    </template>
    <p v-if="message" :role="verified ? 'status' : 'alert'">{{ message }}</p>
    <ion-button v-if="loadFailed" fill="clear" @click="loadRecipients">Retry loading accounts</ion-button>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { IonButton, IonInput } from '@ionic/vue';
import { gql } from '@apollo/client/core';
import { useApolloClient } from '@vue/apollo-composable';

const props = defineProps<{ contractId: string; amount: number }>();
const emit = defineEmits<{ funded: [] }>();
const { client } = useApolloClient();
const recipients = ref<Array<{ provider: string; name: string; accountNumber: string }>>([]);
const receiptUrl = ref('');
const loading = ref(true);
const loadFailed = ref(false);
const busy = ref(false);
const message = ref('');
const verified = ref(false);
const accountsQuery = gql`query EscrowAccounts { escrowRecipients { provider name accountNumber updatedAt } }`;
const fundingMutation = gql`mutation VerifyEscrow($contractId: ID!, $receiptUrl: String!) {
  initiateEscrowPayment(contractId: $contractId, receiptUrl: $receiptUrl) { verified message payment { id status amount } }
}`;

async function loadRecipients() {
  loading.value = true;
  loadFailed.value = false;
  try {
    const { data } = await client.query({ query: accountsQuery, fetchPolicy: 'network-only' });
    recipients.value = data.escrowRecipients || [];
    message.value = '';
  } catch {
    loadFailed.value = true;
    message.value = 'Could not load the receiving accounts. Retry before sending money.';
  } finally { loading.value = false; }
}
async function copyAccount(account: string) {
  try { await navigator.clipboard.writeText(account); message.value = 'Account copied.'; }
  catch { message.value = 'Select and copy the account number shown above.'; }
}
async function verify() {
  if (busy.value) return;
  verified.value = false;
  const value = receiptUrl.value.trim();
  if (!/^https:\/\/(mbreciept\.cbe\.com\.et\/v2-[A-Za-z0-9_-]{8,120}|transactioninfo\.ethiotelecom\.et\/receipt\/[A-Z0-9]{6,40})\/?$/.test(value)) {
    message.value = 'Paste an original HTTPS receipt link from CBE or Telebirr.';
    return;
  }
  busy.value = true;
  message.value = '';
  try {
    const { data } = await client.mutate({ mutation: fundingMutation, variables: { contractId: props.contractId, receiptUrl: value } });
    const result = data?.initiateEscrowPayment;
    verified.value = result?.verified === true;
    message.value = result?.message || 'Payment could not be verified. Keep your receipt and try again.';
    if (verified.value) emit('funded');
  } catch {
    message.value = 'Verification is unavailable. Keep your receipt and retry; do not send another payment.';
  } finally { busy.value = false; }
}
onMounted(loadRecipients);
</script>

<style scoped>
.recipient { border: 1px solid var(--ion-color-medium); padding: 12px; border-radius: 8px; margin: 12px 0; }
.account-number { user-select: text; overflow-wrap: anywhere; }
</style>
