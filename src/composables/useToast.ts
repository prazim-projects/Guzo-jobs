import { toastController } from '@ionic/vue'

export function useToast() {
  const show = async (message: string, color: 'success' | 'danger' | 'warning' = 'success') => {
    const toast = await toastController.create({
      message,
      duration: 3000,
      color,
      position: 'top'
    })
    await toast.present()
  }

  return {
    success: (msg: string) => show(msg, 'success'),
    error: (msg: string) => show(msg, 'danger'),
    warning: (msg: string) => show(msg, 'warning')
  }
}