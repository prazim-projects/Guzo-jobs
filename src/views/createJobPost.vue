<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>New Job Post</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <ion-list>
        <!-- Title Input -->
        <ion-item>
          <ion-label position="stacked">Job Title</ion-label>
          <ion-input v-model="form.title" placeholder="Enter title"></ion-input>
        </ion-item>

        <!-- Post Type Selection -->
        <ion-item>
          <ion-label position="stacked">Post Type</ion-label>
          <ion-select v-model="form.postType" interface="popover">
            <ion-select-option value="Courier">Courier</ion-select-option>
            <ion-select-option value="Transport">Transport</ion-select-option>
            <ion-select-option value="Delivery">Delivery</ion-select-option>
          </ion-select>
        </ion-item>

        <!-- Origin and Destination -->
        <ion-item>
          <ion-label position="stacked">From (Origin)</ion-label>
          <ion-input v-model="form.origin" placeholder="e.g. Addis Ababa"></ion-input>
        </ion-item>

        <ion-item>
          <ion-label position="stacked">To (Destination)</ion-label>
          <ion-input v-model="form.destination" placeholder="e.g. Mizan Teferi"></ion-input>
        </ion-item>

        <!-- Dynamic Expiration Date -->
        <ion-item>
          <ion-label>Expires At</ion-label>
          <ion-datetime-button datetime="datetime"></ion-datetime-button>
          <ion-modal :keep-contents-on-mount="true">
            <ion-datetime 
              id="datetime" 
              v-model="form.expiresAt" 
              presentation="date-time"
            ></ion-datetime>
          </ion-modal>
        </ion-item>

        <!-- Description -->
        <ion-item>
          <ion-label position="stacked">Description</ion-label>
          <ion-textarea 
            v-model="form.description" 
            placeholder="Tell us more..." 
            :auto-grow="true"
          ></ion-textarea>
        </ion-item>
      </ion-list>

      <ion-button expand="block" class="ion-margin-top" @click="handleCreateJob" :disabled="loading">
        <ion-spinner v-if="loading" name="crescent"></ion-spinner>
        <span v-else>Post Job</span>
      </ion-button>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { 
  IonPage, IonHeader, IonToolbar, IonTitle, IonContent, IonList, IonItem, 
  IonLabel, IonInput, IonTextarea, IonSelect, IonSelectOption, IonButton, 
  IonSpinner, IonDatetime, IonDatetimeButton, IonModal, toastController 
} from '@ionic/vue';
import { useMutation } from '@vue/apollo-composable';
import gql from 'graphql-tag';
import { useRouter } from 'vue-router';

const router = useRouter();

//form with empty values
const form = ref({
  title: '',
  postType: 'Courier',
  origin: '',
  destination: '',
  description: '',
  expiresAt: new Date().toISOString() // Defaults to now
});

const CREATE_JOB_MUTATION = gql`
  mutation createJobPost($title: String!, $postType: String!, $origin: String!, $destination: String!, $description: String!, $expiresAt: DateTime!) {
    createJobPost(title: $title, postType: $postType, origin: $origin, destination: $destination, description: $description, expiresAt: $expiresAt) {
      jobPost{
        description
        destination
        expiresAt
        id
        origin
        postType
        title
      }
    }
  }
`

const { mutate: createJob, loading, onDone, onError } = useMutation(CREATE_JOB_MUTATION);

onDone(async () => {
  const toast = await toastController.create({ message: 'Success!', duration: 2000, color: 'success' });
  await toast.present();
  router.replace('/home');
});

onError(async (error) => {
  const toast = await toastController.create({ message: error.message, duration: 3000, color: 'danger' });
  await toast.present();
});

const handleCreateJob = async () => {
  // Logic validation
  if (!form.value.title || !form.value.origin || !form.value.destination) {
    alert("Please fill in all required fields.");
    return;
  }
  try{
    const result = await createJob({
      title: form.value.title,
      postType: form.value.postType,
      origin: form.value.origin,
      destination: form.value.destination,
      description: form.value.description,
      expiresAt: form.value.expiresAt,
    });
  }catch(err){
    console.error("Job creation failed", err);
  }
};

onDone((result) => {
  console.log("Mutation finished:", result.data);
});

onError((err) => {
  console.error("Error details:", err);
});
</script>
