<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/profile"></ion-back-button>
        </ion-buttons>
        <ion-title>Notifications</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <ion-refresher slot="fixed" @ionRefresh="doRefresh($event)">
        <ion-refresher-content pulling-text="Pull to refresh" refreshing-spinner="circles" refreshing-text="Updating data..."></ion-refresher-content>
      </ion-refresher>
      <ion-list v-if="notifications.length">
        <ion-item v-for="item in notifications" :key="item.id" lines="full">
          <ion-label>
            <h2>{{ item.title }}</h2>
            <p>{{ item.message }}</p>
            <p class="meta">{{ item.createdAt }}</p>
          </ion-label>
          <ion-button
            v-if="!item.isRead"
            slot="end"
            fill="outline"
            size="small"
            @click="markAsRead(item.id)"
          >
            Mark read
          </ion-button>
          <ion-badge v-else slot="end" color="success">Read</ion-badge>
        </ion-item>
      </ion-list>

      <ion-text v-else>No notifications yet.</ion-text>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
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
  IonList,
  IonItem,
  IonLabel,
  IonButton,
  IonBadge,
  IonText,
  RefresherCustomEvent,
  toastController,
  onIonViewWillEnter,
} from '@ionic/vue';
import { t } from '@/utils/i18n';

const { client } = useApolloClient();

const MY_NOTIFICATIONS = gql`
  query MyNotifications {
    myNotifications {
      id
      title
      message
      isRead
      createdAt
      type
    }
  }
`;

const MARK_READ = gql`
  mutation MarkNotificationRead($notificationId: ID!) {
    markNotificationRead(notificationId: $notificationId) {
      notification {
        id
        isRead
      }
    }
  }
`;

const { result, refetch } = useQuery(MY_NOTIFICATIONS, null, {
  fetchPolicy: 'cache-first',
});

onIonViewWillEnter(async () => {
  await refetch();
});

const notifications = computed(() => result.value?.myNotifications || []);

const doRefresh = async (event: RefresherCustomEvent) => {
  try {
    await refetch();
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

const markAsRead = async (notificationId: string) => {
  await client.mutate({
    mutation: MARK_READ,
    variables: { notificationId },
  });
  await refetch();
};
</script>

<style scoped>
.meta {
  font-size: 0.8rem;
  color: var(--ion-color-medium);
}
</style>
