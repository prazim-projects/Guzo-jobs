import { ref } from 'vue';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

export interface NativeImageCaptureResult {
  dataUrl: string;
  mimeType: string;
}

export const useNativeImageCapture = () => {
  const imageDataUrl = ref('');
  const mimeType = ref('image/jpeg');
  const capturing = ref(false);

  const capture = async (source: CameraSource = CameraSource.Camera): Promise<NativeImageCaptureResult | null> => {
    capturing.value = true;
    try {
      const photo = await Camera.getPhoto({
        resultType: CameraResultType.DataUrl,
        source,
        quality: 85,
        width: 1600,
        allowEditing: false,
      });

      if (!photo.dataUrl) {
        return null;
      }

      imageDataUrl.value = photo.dataUrl;
      mimeType.value = photo.format ? `image/${photo.format.toLowerCase()}` : 'image/jpeg';
      return { dataUrl: photo.dataUrl, mimeType: mimeType.value };
    } finally {
      capturing.value = false;
    }
  };

  const clear = () => {
    imageDataUrl.value = '';
    mimeType.value = 'image/jpeg';
  };

  return {
    imageDataUrl,
    mimeType,
    capturing,
    captureFromCamera: () => capture(CameraSource.Camera),
    pickFromGallery: () => capture(CameraSource.Photos),
    clear,
  };
};
