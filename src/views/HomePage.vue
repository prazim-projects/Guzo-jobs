<template>
  <ion-page>
    
    <ion-content >
    
      <div>
        <div class="hero ion-padding">
        <h1 class="title">Welcome to Guzo Jobs 🌍</h1>
        <p class="subtitle">Odd job for travellers!</p>
        </div>
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
                  Origin Location: {{ note.origin }}
                </ion-card-subtitle>
              </ion-card-header>
              <ion-card-content>
                Going TO: {{ note.destination }}
              </ion-card-content>
              <ion-card-content>
              <ion-buttons slot="end">
                <ion-button
                  v-for="action in actions"
                  :key="action.name"
                  @click="action.onClick">
                  <ion-icon :name="action.icon"></ion-icon>
                </ion-button>
              </ion-buttons>
            </ion-card-content>
            </ion-card>
          </ion-col>
        </ion-row>
      </ion-grid>
    </ion-content>
    <floatingPostButton class="fbutton" />
    
    <appHeader :routes="navRoutes" :show-menu="true" />
  </ion-page>
</template>

<script lang="ts" setup>
import floatingPostButton from '@/components/floatingPostButton.vue'
import AppHeader from '@/components/appFoot.vue'
import {
  IonPage,
  IonContent,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonGrid,
  IonRow, 
  IonCol,
  IonIcon,
  IonButton,
  IonButtons
} from '@ionic/vue'
import { useRouter } from 'vue-router'
import { add } from 'ionicons/icons'
import { icon } from 'leaflet'



// Mock demo data
interface Note {
  id: number
  title: string
  origin: string
  destination: string
  image: string
  
}

const navRoutes = [
  { path: '/', label: 'Home', icon: 'home-outline' },
  { path: '/add', label: 'Add Note', icon: 'add' },
  { path: '/login', label: 'Login', icon: 'log-in-outline' },
  { path: '/profile', label: 'Profile', icon: 'person-circle-outline' },
  { path: '/mapET', label: 'Map ET', icon: 'map-outline' },
  { path: '/signup', label: 'Signup', icon: 'person-add-outline' },
];

const actions = [
   { name: "comment", icon: "chatbubble", onClick: () => console.log("Comment") },
  { name: "share", icon: "share", onClick: () => console.log("Shared!") },
  {name: "route", icon: "compass", onClick: () => console.log("Route!") },
];


const demoNotes: Note[] = [
  {
    id: 1,
    title: 'Going to Addis Ababa from Adama',
    origin: 'Adama',
    destination: 'Addis Ababa',
    image: 'https://picsum.photos/seed/mojo/400/250',
    
  },
  {
    id: 2,
    title: 'Going to Gondar, from Dessie, I can deliver small items',
    origin: 'Dessie',
    destination: 'Gondar',
    image: 'https://picsum.photos/seed/amhara/400/250',

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

.fbutton {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  padding-bottom: 30px;
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
