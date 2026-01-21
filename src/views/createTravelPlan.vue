<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>Create Travel Plan</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <ion-item>
        <ion-input v-model="origin" label="Origin" placeholder="e.g. Adama" />
      </ion-item>

      <ion-item>
        <ion-input v-model="destination" label="Destination" placeholder="e.g. Gondar" />
      </ion-item>

      <ion-item>
        <ion-datetime
          presentation="date"
          v-model="departureDate"
          label="Departure Date"
        />
      </ion-item>

      <ion-item>
        <ion-input
          type="number"
          v-model.number="maxCapacity"
          label="Max Capacity (optional)"
        />
      </ion-item>

      <ion-item>
        <ion-textarea
          v-model="notes"
          label="Notes"
          placeholder="Any delivery notes?"
        />
      </ion-item>

      <ion-button expand="block" @click="submit">
        Create Travel Plan
      </ion-button>
    </ion-content>
  </ion-page>
</template>
<script>
    import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonItem,
  IonInput,
  IonTextarea,
  IonDatetime,
  IonButton
} from '@ionic/vue'

import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const origin = ref('')
const destination = ref('')
const departureDate = ref('')
const maxCapacity = ref<number | null>(null)
const notes = ref('')

</script>