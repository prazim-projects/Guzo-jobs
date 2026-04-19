import { onMounted, ref, watch } from 'vue';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { loadCachedPhotos, persistPhotos, savePhoto, type StoredPhoto } from '@/utils/photoStorage';

export type UserPhoto = StoredPhoto;

export const usePhotoGallery = () => {
  const photos = ref<UserPhoto[]>([]);

  const cachePhotos = async () => {
    await persistPhotos(photos.value);
  };

  const takePhoto = async () => {
    const photo = await Camera.getPhoto({
      resultType: CameraResultType.Uri,
      source: CameraSource.Camera,
      quality: 90,
    });

    const fileName = `${Date.now()}.jpeg`;
    const savedFileImage = await savePhoto(photo, fileName);
    photos.value = [savedFileImage, ...photos.value];
  };

  const loadSaved = async () => {
    photos.value = await loadCachedPhotos();
  };

  watch(photos, () => {
    void cachePhotos();
  }, { deep: true });

  onMounted(() => {
    void loadSaved();
  });

  return {
    takePhoto,
    photos,
  };
};
