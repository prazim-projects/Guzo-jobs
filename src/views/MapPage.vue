<template>
    <IonPage>
        <AppFoot />
        <IonContent>
            <IonGrid>
                <IonRow>
                    <IonCol size="12">
                        <IonCard>
                            <div id="map" style="height: 500px;"></div>
                        </IonCard>
                    </IonCol>
                </IonRow>
            </IonGrid>
        </IonContent>
    </IonPage>

</template>

<script lang="ts" setup>
import L, {Map as LeafletMap} from 'leaflet';
import { onMounted } from 'vue';
import { IonPage, IonContent, IonGrid, IonRow, IonCol, IonCard } from '@ionic/vue';
import AppFoot from '@/components/appFoot.vue';

let map: LeafletMap;


onMounted(() => {
    // set ET bounds
    const mapEthiopia: L.LatLngBoundsExpression = [
        [3.4, 32.9], //SouthWest
        [14.9, 48.2]  //NorthEast
    ];

    const center: L.LatLngTuple = [9.05, 38.189673];
    // Init map
    // map = L.map('map').setView([9.145, 40.489673], 6); // Centered on Ethiopia
    
    map = L.map('map', {
        center,
        zoom: 6,
        maxBounds: mapEthiopia,
        maxBoundsViscosity: 1.0
    })

    // openstreetmap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
    }).addTo(map);

    // sample circle marker
    const cities: {name: string, coords: L.LatLngTuple}[] = [
        { name: 'Addis Ababa', coords: [9.03, 38.74] },
        { name: 'Dire Dawa', coords: [9.6, 41.85] },
        { name: 'Mekelle', coords: [13.5, 39.47] },
        { name: 'Gondar', coords: [12.6, 37.47] },
        { name: 'Bahir Dar', coords: [11.6, 37.38] },
        { name: 'Hawassa', coords: [7.06, 38.47] },
        { name: 'Jijiga', coords: [9.35, 42.8] },
        { name: 'Harar', coords: [9.31, 42.12] },
        { name: 'Axum', coords: [14.13, 38.72] },
        { name: 'Lalibela', coords: [12.03, 39.03]}
    ];

    cities.forEach(city => {
        L.marker(city.coords).addTo(map)
            .bindPopup(city.name)

    })
})
</script>

<style scoped>
#map {
  width: 100%;
  height: 100%;
}
</style>