<template>
  <ion-page>
    <ion-content class="onboarding-content" :scroll-y="false">
      <!-- Skip button -->
      <ion-button
        fill="clear"
        class="skip-button"
        @click="skipOnboarding"
      >
        Skip
      </ion-button>

      <!-- Slides -->
      <div class="swiper onboarding-swiper">
        <div class="swiper-wrapper">
          <!-- Slide 1: Welcome -->
          <div class="swiper-slide slide">
            <div class="slide-content">
              <div class="slide-image">
                <ion-icon name="airplane-outline" size="large" color="primary"></ion-icon>
              </div>
              <h1 class="slide-title">Welcome to Guzo Jobs</h1>
              <p class="slide-description">
                Connect travelers with locals for odd jobs and deliveries.
                Earn money while traveling or get help with your tasks.
              </p>
            </div>
          </div>

          <!-- Slide 2: Post Jobs -->
          <div class="swiper-slide slide">
            <div class="slide-content">
              <div class="slide-image">
                <ion-icon name="add-circle-outline" size="large" color="primary"></ion-icon>
              </div>
              <h1 class="slide-title">Post Jobs</h1>
              <p class="slide-description">
                Need something delivered or want to hire help?
                Post your job with details, location, and price.
                Travelers in your area will see your posting.
              </p>
            </div>
          </div>

          <!-- Slide 3: Find Opportunities -->
          <div class="swiper-slide slide">
            <div class="slide-content">
              <div class="slide-image">
                <ion-icon name="search-outline" size="large" color="primary"></ion-icon>
              </div>
              <h1 class="slide-title">Find Opportunities</h1>
              <p class="slide-description">
                Browse available jobs in your area. Apply for tasks that
                match your schedule and earn money while exploring new places.
              </p>
            </div>
          </div>

          <!-- Slide 4: Safe & Secure -->
          <div class="swiper-slide slide">
            <div class="slide-content">
              <div class="slide-image">
                <ion-icon name="shield-checkmark-outline" size="large" color="primary"></ion-icon>
              </div>
              <h1 class="slide-title">Safe & Secure</h1>
              <p class="slide-description">
                Built-in messaging, job tracking, and completion confirmation
                ensure both parties are protected. Mark jobs as completed
                only when satisfied with the work.
              </p>
            </div>
          </div>

          <!-- Slide 5: Get Started -->
          <div class="swiper-slide slide">
            <div class="slide-content">
              <div class="slide-image">
                <ion-icon name="rocket-outline" size="large" color="primary"></ion-icon>
              </div>
              <h1 class="slide-title">Ready to Get Started?</h1>
              <p class="slide-description">
                Join our community of travelers and locals.
                Start earning or get help with your tasks today!
              </p>
              <ion-button
                expand="block"
                size="large"
                class="get-started-button"
                @click="completeOnboarding"
              >
                <ion-icon slot="start" name="checkmark-circle"></ion-icon>
                Get Started
              </ion-button>
            </div>
          </div>
        </div>
        <div class="swiper-pagination"></div>
      </div>

      <!-- Navigation dots indicator -->
      <div class="pagination-container">
        <div
          v-for="(slide, index) in slides"
          :key="index"
          class="pagination-dot"
          :class="{ active: currentSlide === index }"
        ></div>
      </div>

      <!-- Back button (shown on all slides except first) -->
      <div v-if="currentSlide > 0" class="back-button-container">
        <ion-button
          fill="clear"
          class="back-button"
          @click="backSlide"
        >
          <ion-icon slot="start" name="arrow-back"></ion-icon>
          Back
        </ion-button>
      </div>

      <!-- Next button (shown on all slides except last) -->
      <div v-if="currentSlide < slides.length - 1" class="next-button-container">
        <ion-button
          fill="clear"
          class="next-button"
          @click="nextSlide"
        >
          Next
          <ion-icon slot="end" name="arrow-forward"></ion-icon>
        </ion-button>
      </div>
    </ion-content>
  </ion-page>
</template>

<script lang="ts" setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  IonPage,
  IonContent,
  IonButton,
  IonIcon
} from '@ionic/vue'

// Import Swiper
import Swiper from 'swiper'
import { Pagination } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/pagination'

const router = useRouter()
let swiper: Swiper | null = null
const currentSlide = ref(0)

const slides = [
  { title: 'Welcome' },
  { title: 'Post Jobs' },
  { title: 'Find Opportunities' },
  { title: 'Safe & Secure' },
  { title: 'Get Started' }
]

const onSlideChange = () => {
  if (swiper) {
    currentSlide.value = swiper.activeIndex
  }
}

const nextSlide = () => {
  if (swiper) {
    swiper.slideNext()
  }
}

const backSlide = () => {
  if (swiper) {
    swiper.slidePrev()
  }
}

const skipOnboarding = () => {
  localStorage.setItem('onboardingCompleted', 'true')
  router.replace('/home')
}

const completeOnboarding = () => {
  localStorage.setItem('onboardingCompleted', 'true')
  router.replace('/home')
}

onMounted(() => {
  // Check if user has already completed onboarding
  const completed = localStorage.getItem('onboardingCompleted')
  if (completed === 'true') {
    router.replace('/home')
  }

  // Initialize swiper after component is mounted
  nextTick(() => {
    const swiperEl = document.querySelector('.onboarding-swiper')
    if (swiperEl) {
      swiper = new Swiper(swiperEl as HTMLElement, {
        modules: [Pagination],
        slidesPerView: 1,
        spaceBetween: 0,
        pagination: {
          el: '.swiper-pagination',
          clickable: true,
        },
        autoplay: false,
        on: {
          slideChange: onSlideChange
        }
      })
      console.log('Swiper initialized:', swiper)
    }
  })
})
</script>

<style scoped>
.onboarding-content {
  --background: linear-gradient(135deg, var(--ion-color-primary) 0%, var(--ion-color-secondary) 100%);
  position: relative;
}

.skip-button {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
  --color: white;
  font-weight: 600;
}

.onboarding-swiper {
  height: calc(100vh - 80px);
  width: 100%;
}

.slide {
  display: flex;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 80px);
  padding: 20px;
}

.slide-content {
  text-align: center;
  max-width: 300px;
  color: white;
}

.slide-image {
  margin-bottom: 40px;
}

.slide-image ion-icon {
  font-size: 80px;
  opacity: 0.9;
}

.slide-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 20px;
  line-height: 1.2;
}

.slide-description {
  font-size: 16px;
  line-height: 1.6;
  opacity: 0.9;
  margin-bottom: 30px;
}

.get-started-button {
  --background: white;
  --color: var(--ion-color-primary);
  --border-radius: 12px;
  font-weight: 600;
  margin-top: 20px;
}

.pagination-container {
  position: absolute;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}

.pagination-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
}

.pagination-dot.active {
  background-color: white;
  transform: scale(1.2);
}

.next-button-container {
  position: absolute;
  bottom: 40px;
  right: 20px;
  z-index: 10;
}

.next-button {
  --color: white;
  font-weight: 600;
}

.back-button-container {
  position: absolute;
  bottom: 40px;
  left: 20px;
  z-index: 10;
}

.back-button {
  --color: white;
  font-weight: 600;
}

/* Swiper styles */
.swiper {
  width: 100%;
  height: 100%;
}

.swiper-slide {
  display: flex;
  align-items: center;
  justify-content: center;
}

.swiper-pagination {
  bottom: 120px !important;
}

.swiper-pagination-bullet {
  width: 8px;
  height: 8px;
  background-color: rgba(255, 255, 255, 0.5);
  opacity: 1;
  margin: 0 4px;
}

.swiper-pagination-bullet-active {
  background-color: white;
  transform: scale(1.2);
}
</style>