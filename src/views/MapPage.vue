<template>
  <ion-page>
    <ion-header v-if="!isFullscreen">
      <ion-toolbar color="primary">
        <ion-title>Map of Ethiopia</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="toggleFullscreen">
            <ion-icon :icon="isFullscreen ? contractOutline : expandOutline"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content :fullscreen="true" :class="{ 'fullscreen-map': isFullscreen }">
      <div ref="mapContainer" class="map-container"></div>
    </ion-content>

    <!-- <AppFoot /> -->
  </ion-page>
</template>

<script lang="ts" setup>
import L, { Map as LeafletMap, LatLngBoundsExpression, LatLngTuple } from 'leaflet';
import 'leaflet/dist/leaflet.css'; // Fixes gray tiles and rendering bugs
import { onUnmounted, ref } from 'vue';
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonIcon,
  IonContent,
  IonFooter,
  onIonViewDidEnter,
  onIonViewWillLeave,
} from '@ionic/vue';
import { expandOutline, contractOutline } from 'ionicons/icons';

let map: LeafletMap | null = null;
const mapContainer = ref<HTMLDivElement | null>(null);
const isFullscreen = ref(false);

const initializeMap = () => {
  if (!mapContainer.value || map) return; // Prevent re-init

  const ethiopiaBounds: LatLngBoundsExpression = [
    [3.4, 32.9], // Southwest
    [14.9, 48.2], // Northeast
  ];

  const center: LatLngTuple = [9.05, 38.189673];

  map = L.map(mapContainer.value, {
    center,
    zoom: 6,
    maxBounds: ethiopiaBounds,
    maxBoundsViscosity: 1.0,
    zoomControl: true, // Enable for mobile pinch-zoom
    attributionControl: true,
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
    tileSize: 256, // Standard, but can optimize for mobile
    noWrap: true, // Prevent wrapping around globe
  }).addTo(map);

  map.fitBounds(ethiopiaBounds);
  const minZoom = map.getBoundsZoom(ethiopiaBounds, true);
  map.setMinZoom(minZoom);

  // Sample markers (batch add for perf)
  const cities: { name: string; coords: LatLngTuple }[] = [
    { name: 'Addis Ababa', coords: [9.03, 38.74] },
    { name: 'Dire Dawa', coords: [9.6, 41.85] },
    { name: 'Mekelle', coords: [13.5, 39.47] },
    { name: 'Gondar', coords: [12.6, 37.47] },
    { name: 'Bahir Dar', coords: [11.6, 37.38] },
    { name: 'Hawassa', coords: [7.06, 38.47] },
    { name: 'Jijiga', coords: [9.35, 42.8] },
    { name: 'Harar', coords: [9.31, 42.12] },
    { name: 'Axum', coords: [14.13, 38.72] },
    { name: 'Lalibela', coords: [12.03, 39.03] },
  ];

  const markerLayer = L.layerGroup();
  cities.forEach((city) => {
    L.marker(city.coords).bindPopup(city.name).addTo(markerLayer);
  });
  markerLayer.addTo(map); // Add all at once
};

const destroyMap = () => {
  if (map) {
    map.remove();
    map = null;
  }
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
  setTimeout(() => {
    if (map) map.invalidateSize();
  }, 100); // Shorter delay for mobile responsiveness
};

// Ionic lifecycle: Init on view enter, destroy on leave
onIonViewDidEnter(() => {
  initializeMap();
  if (map) map.invalidateSize();
});

onIonViewWillLeave(destroyMap);

onUnmounted(destroyMap);

// Handle resize/orientation (debounced for perf)
let resizeTimeout: NodeJS.Timeout | null = null;
const handleResize = () => {
  if (resizeTimeout) clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    if (map) map.invalidateSize();
  }, 100);
};
window.addEventListener('resize', handleResize);
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (resizeTimeout) clearTimeout(resizeTimeout);
});
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  will-change: transform; /* Enable GPU acceleration */
}

.fullscreen-map {
  --offset-top: 0 !important;
}

ion-content::part(scroll) {
  height: 100%;
  overflow: hidden; /* Prevent scroll bounce on mobile */
}
</style>