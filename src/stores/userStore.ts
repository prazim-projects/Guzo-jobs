import { defineStore } from "pinia";
import { ref } from "vue";

export const useUserStore = defineStore("user", () => {
    const username = ref<string | null>(null);
    const isLoggedIn = ref<boolean>(false);
    const token =ref<string | null>(null);

    function login(name: string, password: string) {
        username.value = name;
        isLoggedIn.value = true;
    }

    function logout() {
        username.value = null;
        isLoggedIn.value = false;
    }

  return { username, isLoggedIn, login, logout };
});