<template>
  <main class="welcome" aria-label="Welcome to Guzo Jobs">
    <header><button type="button" @click="emit('complete')">{{ labels.skip }}</button></header>
    <div ref="carousel" class="slides" @scroll.passive="onScroll" @keydown.left.prevent="go(current - 1)" @keydown.right.prevent="go(current + 1)">
      <section v-for="(slide, index) in slides" :key="slide.title" class="slide" :aria-label="`${index + 1} of ${slides.length}: ${slide.title}`" :inert="index !== current">
        <div class="slide-content">
          <svg class="slide-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="slide.icon" /></svg>
          <h1 class="slide-title">{{ slide.title }}</h1>
          <p class="slide-description">{{ slide.description }}</p>
          <button v-if="index === slides.length - 1" type="button" class="start" @click="emit('complete')">{{ labels.start }}</button>
        </div>
      </section>
    </div>
    <footer>
      <nav class="dots" aria-label="Welcome slides">
        <button v-for="(slide, index) in slides" :key="slide.title" type="button" :aria-label="`Go to slide ${index + 1}: ${slide.title}`" :aria-current="current === index ? 'step' : undefined" @click="go(index)"><span /></button>
      </nav>
      <p class="sr-only" aria-live="polite">{{ current + 1 }} of {{ slides.length }}: {{ slides[current].title }}</p>
      <div class="navigation">
        <button type="button" :disabled="current === 0" @click="go(current - 1)">{{ labels.back }}</button>
        <button v-if="current < slides.length - 1" type="button" @click="go(current + 1)">{{ labels.next }} →</button>
      </div>
    </footer>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue';
const emit = defineEmits<{ complete: [] }>();
const current = ref(0);
const carousel = ref<HTMLElement>();
// Keep the full application's translation dictionary off the welcome path.
const labels = localStorage.getItem('app_language') === 'am'
  ? { skip: 'ዝለል', start: 'ጀምር', back: 'ተመለስ', next: 'ቀጣይ' }
  : { skip: 'Skip', start: 'Get Started', back: 'Back', next: 'Next' };
const slides = [
  { title: 'Welcome to Guzo Jobs', description: 'Connect travelers with locals for odd jobs and deliveries. Earn money while traveling or get help with your tasks.', icon: 'M22 2 9 15M22 2 14 22 9 15 2 10Z' },
  { title: 'Post Jobs', description: 'Need something delivered or want to hire help? Post your job with details, location, and price. Travelers in your area will see your posting.', icon: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 8v8M8 12h8' },
  { title: 'Find Opportunities', description: 'Browse available jobs in your area. Apply for tasks that match your schedule and earn money while exploring new places.', icon: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 15l7 7' },
  { title: 'Safe & Secure', description: 'Job tracking and completion confirmation help both parties follow the work. Mark jobs as completed only when satisfied with the work.', icon: 'M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6ZM8 12l3 3 5-6' },
  { title: 'Ready to Get Started?', description: 'Join our community of travelers and locals. Start earning or get help with your tasks today!', icon: 'M4 12l5 5L20 6' },
];
function go(index: number) {
  if (!carousel.value) return;
  const next = Math.max(0, Math.min(slides.length - 1, index));
  carousel.value.scrollTo({ left: next * carousel.value.clientWidth, behavior: 'auto' });
  current.value = next;
}
function onScroll() {
  if (carousel.value?.clientWidth) current.value = Math.max(0, Math.min(slides.length - 1, Math.round(carousel.value.scrollLeft / carousel.value.clientWidth)));
}
</script>

<style scoped>
.welcome { position: fixed; inset: 0; display: flex; flex-direction: column; background: linear-gradient(135deg, #0644a6, #086b91); color: #fff; font-family: system-ui, sans-serif; line-height: 1.5; overflow-y: auto; }
.welcome * { box-sizing: border-box; }
header { display: flex; justify-content: flex-end; padding: max(12px, env(safe-area-inset-top)) 16px 0; }
button { font: inherit; font-weight: 600; color: inherit; background: transparent; border: 0; border-radius: 8px; min-height: 44px; min-width: 44px; padding: 10px 16px; cursor: pointer; }
button:focus-visible { outline: 3px solid #fff; outline-offset: -3px; }
button:disabled { visibility: hidden; }
.slides { flex: 1 0 360px; display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; }
.slides::-webkit-scrollbar { display: none; }
.slide { flex: 0 0 100%; min-width: 0; scroll-snap-align: start; display: flex; align-items: center; justify-content: center; padding: 16px 24px; }
.slide-content { width: 100%; max-width: 340px; text-align: center; }
.slide-icon { width: 72px; height: 72px; margin-bottom: 20px; }
.slide-title { font-size: 28px; line-height: 1.2; margin: 0 0 20px; }
.slide-description { font-size: 16px; margin: 0 0 20px; }
.start { background: #fff; color: #0644a6; width: 100%; }
footer { flex-shrink: 0; padding: 0 16px max(16px, env(safe-area-inset-bottom)); }
.dots { display: flex; justify-content: center; }
.dots button { padding: 16px; }
.dots span { display: block; width: 8px; height: 8px; border-radius: 50%; background: #ffffff70; }
.dots [aria-current] span { background: #fff; transform: scale(1.25); }
.navigation { display: flex; justify-content: space-between; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
</style>
