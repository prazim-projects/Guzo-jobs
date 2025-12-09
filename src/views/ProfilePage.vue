<script lang="ts" setup>
import { useRouter } from 'vue-router';
import { IonContent, IonPage } from '@ionic/vue';
import appHeader from '@/components/appFoot.vue';
const router = useRouter();

</script>

<template>
    <ion-page>
        <appHeader />
        <ion-content ion-padding>
            <h1>Profile Page</h1>
            <p>This is the profile page.</p>
        </ion-content>
    </ion-page>
</template>


