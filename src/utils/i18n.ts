import { ref } from 'vue'

export type AppLanguage = 'en' | 'am'

type TranslationKey =
  | 'refresh_notice'
  | 'refresh_done'
  | 'lang_switch_to_am'
  | 'lang_switch_to_en'

const dictionary: Record<AppLanguage, Record<TranslationKey, string>> = {
  en: {
    refresh_notice: 'Pull down to refresh is available on every page.',
    refresh_done: 'Updated successfully.',
    lang_switch_to_am: 'Switch to Amharic',
    lang_switch_to_en: 'Switch to English',
  },
  am: {
    refresh_notice: 'በሁሉም ገፆች ላይ ለማዘመን ወደ ታች ይጎትቱ።',
    refresh_done: 'መረጃው ተዘምኗል።',
    lang_switch_to_am: 'ወደ አማርኛ ቀይር',
    lang_switch_to_en: 'ወደ እንግሊዝኛ ቀይር',
  },
}

const stored = (localStorage.getItem('app_language') as AppLanguage | null)
export const currentLanguage = ref<AppLanguage>(stored === 'am' ? 'am' : 'en')

export const setLanguage = (next: AppLanguage) => {
  currentLanguage.value = next
  localStorage.setItem('app_language', next)
}

export const toggleLanguage = () => {
  setLanguage(currentLanguage.value === 'en' ? 'am' : 'en')
}

export const t = (key: TranslationKey): string => {
  return dictionary[currentLanguage.value][key] || dictionary.en[key]
}
