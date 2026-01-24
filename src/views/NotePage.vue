<template>
    <ion-page>
        <ion-content>            
            <h1>Add Note</h1>
            <ion-item>
                <ion-input v-model="newNote" placeholder="Enter your note"></ion-input>
            </ion-item>
            <ion-grid>
                <ion-row>
                    <ion-col size="6" size-md="4" size-lg="3" v-for="photo in photos" :key="photo.filepath">
                        <ion-img :src="photo.webviewPath"></ion-img>
                    </ion-col>
                </ion-row>
            </ion-grid>
            <ion-fab vertical="bottom" horizontal="center" slot="fixed">
                <ion-fab-button @click="takePhoto()">
                    <ion-icon :icon="camera"></ion-icon>
                </ion-fab-button>
            </ion-fab>
        </ion-content>
    </ion-page>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import {camera, trash, close} from 'ionicons/icons';
import { IonContent, IonItem, IonInput, IonIcon, IonFab, IonFabButton, IonGrid, IonImg, IonRow, IonCol, IonPage } from '@ionic/vue';
import { usePhotoGallery, UserPhoto } from '@/composables/usePhotoGallery';
import { useRouter } from 'vue-router';


const newNote = ref('');
const { photos, takePhoto } = usePhotoGallery();
// const { takePhoto, photos, deletePhoto } = usePhotoGallery();

const router = useRouter()


function addNote() {
    console.log("Note added:", newNote.value);
}

</script>

<style scoped>

</style>