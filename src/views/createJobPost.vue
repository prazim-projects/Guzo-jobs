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
          <ion-label position="stacked">የሥራ ርዕስ</ion-label>
          <ion-input v-model="form.title" placeholder="Enter title"></ion-input>
        </ion-item>

        <!-- Post Type Selection -->
        <ion-item>
          <ion-label position="stacked">Post Type</ion-label>
          <ion-select v-model="form.postType" interface="popover">
            <ion-select-option value="Transport">Transport</ion-select-option>
            <ion-select-option value="Delivery">Delivery</ion-select-option>
            <ion-select-option value="Odd Job"> Odd Job</ion-select-option>
            <ion-select-option value="Trade">Trade</ion-select-option>
          </ion-select>
        </ion-item>

        <!-- Origin and Destination -->
        <ion-item>
          <ion-label position="stacked">From (Origin)</ion-label>
          <ion-input v-model="form.origin" placeholder="e.g. Addis Ababa"></ion-input>
        </ion-item>

        <ion-item v-if="form.postType !== 'Odd Job' && form.postType !== 'Trade'">
          <ion-label position="stacked">To (Destination)</ion-label>
          <ion-input v-model="form.destination" placeholder="e.g. Hawassa"></ion-input>
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
        <ion-item>
          <ion-label position="stacked">Price</ion-label>
          <ion-input
            v-model="priceInput"
            type="number"
            inputmode="decimal"
            placeholder="1000 ETB"
          ></ion-input>
        </ion-item>

        <ion-item>
          <ion-label position="stacked">Product Image (optional)</ion-label>
          <div class="image-actions">
            <ion-button size="small" fill="outline" @click="captureProductImage" :disabled="capturing">
              Capture Photo
            </ion-button>
            <ion-button size="small" fill="outline" @click="pickProductImage" :disabled="capturing">
              Choose From Gallery
            </ion-button>
          </div>
          <input type="file" accept="image/*" @change="onImageSelected" />
        </ion-item>

        <div v-if="form.productImage" class="preview-frame">
          <img :src="form.productImage" alt="Product preview" class="preview-image" loading="lazy" />
        </div>
      </ion-list>

      <ion-item>
        <ion-label position="stacked">Expires At</ion-label>
        <ion-datetime v-model="form.expiresAt" presentation="date-time"></ion-datetime>
      </ion-item>

      <ion-button expand="block" class="ion-margin-top" @click="handleCreateJob" :disabled="loading">
        <ion-spinner v-if="loading" name="crescent"></ion-spinner>
        <span v-else>Post Job</span>
      </ion-button>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { 
  IonPage, IonHeader, IonToolbar, IonTitle, IonContent, IonList, IonItem, 
  IonLabel, IonInput, IonTextarea, IonSelect, IonSelectOption, IonButton, 
  IonSpinner, IonDatetime, toastController
} from '@ionic/vue';
import { useMutation } from '@vue/apollo-composable';
import gql from 'graphql-tag';
import { useRouter } from 'vue-router';
import { useNativeImageCapture } from '@/composables/useNativeImageCapture';

const router = useRouter();

//form with empty values
const form = ref({
  title: '',
  postType: 'Delivery',
  origin: '',
  destination: '',
  description: '',
  productImage: '',
  price: 0,
  expiresAt: new Date().toISOString()
});

const priceInput = computed({
  get: () => String(form.value.price || ''),
  set: (value: string) => {
    form.value.price = Number(value) || 0;
  }
});

const { imageDataUrl, capturing, captureFromCamera, pickFromGallery } = useNativeImageCapture();

const CREATE_JOB_MUTATION = gql`
  mutation createJobPost($title: String!, $postType: String!, $origin: String!, $destination: String!, $description: String!, $expiresAt: DateTime!, $price: Int!) {
    createJobPost(title: $title, postType: $postType, origin: $origin, destination: $destination, description: $description, expiresAt: $expiresAt, price: $price) {
      jobPost{
        description
        destination
        expiresAt
        id
        origin
        postType
        title
        price
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

const onImageSelected = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    form.value.productImage = String(reader.result || '');
    imageDataUrl.value = form.value.productImage;
  };
  reader.readAsDataURL(file);
};

const applyCapturedImage = async (action: () => Promise<{ dataUrl: string; mimeType: string } | null>) => {
  const result = await action();
  if (result?.dataUrl) {
    form.value.productImage = result.dataUrl;
  }
};

const captureProductImage = () => applyCapturedImage(captureFromCamera);
const pickProductImage = () => applyCapturedImage(pickFromGallery);

const handleCreateJob = async () => {
  const isLocalJob = form.value.postType === 'Odd Job' || form.value.postType === 'Trade';
  
  if (isLocalJob) {
    form.value.destination = form.value.origin;
  } else if (!form.value.destination) {
    alert("Please enter a destination.");
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
      price: form.value.price,
    });
  }catch(err){
    console.error("Job creation failed", err);
  }
};


</script>

<style scoped>
.preview-image {
  width: 100%;
  height: 160px;
  object-fit: contain;
  border-radius: 10px;
  background: #f4f6f8;
}

.preview-frame {
  margin-top: 10px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.image-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
</style>
