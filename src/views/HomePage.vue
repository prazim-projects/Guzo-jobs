<template>
  <ion-page>
    <ion-header translucent>
      <ion-toolbar color="primary">
        <ion-title>GeoNotes</ion-title>
      </ion-toolbar>
    </ion-header>

    
    <!-- Content -->
    <ion-content fullscreen>
      <div class="hero ion-padding">
        <h1 class="title">Welcome to Your Travel Diary 🌍</h1>
        <p class="subtitle">Capture places, memories, and moments. Share, interact, route publish</p>
      </div>

      <!-- Notes List -->
      <ion-grid>
        <ion-row>
          <ion-col
            size="12"
            size-md="6"
            size-sm="4"
            v-for="note in demoNotes"
            :key="note.id"
          >
            <ion-card @click="openNote(note)">
              <img :src="note.image" alt="Note Image" width="200px" />
              <ion-card-header>
                <ion-card-title>{{ note.title }}</ion-card-title>
                <ion-card-subtitle>
                  {{ note.location }}
                </ion-card-subtitle>
              </ion-card-header>
              <ion-card-content>
                {{ note.description }}
              </ion-card-content>
            </ion-card>
          </ion-col>
        </ion-row>
      </ion-grid>

      <!-- Floating Action Button -->
      <ion-fab slot="fixed" vertical="bottom" horizontal="end">
        <ion-fab-button color="tertiary" @click="goToAddNote">
          <ion-icon name="add"></ion-icon>
        </ion-fab-button>
      </ion-fab>
    </ion-content>
  </ion-page>
</template>

<script lang="ts" setup>
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonGrid,
  IonRow,
  IonCol,
  IonFab,
  IonFabButton,
  IonIcon,
} from '@ionic/vue'
import { useRouter } from 'vue-router'
import { images, square, triangle } from 'ionicons/icons';

// Mock demo data
interface Note {
  id: number
  title: string
  description: string
  image: string
  location: string
}

const demoNotes: Note[] = [
  {
    id: 1,
    title: 'Addis Ababa Adventure',
    description: 'Explored Entoto Mountains and had the best coffee.',
    image: 'https://picsum.photos/seed/addis/400/250',
    location: 'Addis Ababa, Ethiopia',
  },
  {
    id: 2,
    title: 'Blue Nile Falls',
    description: 'Got drenched but it was worth it!',
    image: 'https://picsum.photos/seed/bahirdar/400/250',
    location: 'Bahir Dar, Ethiopia',
  },
]

const router = useRouter()

function goToAddNote() {
  router.push('/add')
}

function openNote(note: Note) {
  console.log('Opening note:', note)
}
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
