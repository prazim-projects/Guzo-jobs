<template>
<ion-fab vertical="bottom" horizontal="end" slot="fixed">
    <ion-fab-button color="primary" router-link="/add">
      <ion-icon name="add"></ion-icon>
    </ion-fab-button>
  </ion-fab>
</template>

<script lang="ts" setup>
import { IonFab, IonFabButton, IonIcon } from '@ionic/vue';



</script>

<style lang="css">
ion-fab-button {
  --box-shadow: 0 4px 16px rgba(0,0,0,0.25);
}

</style>