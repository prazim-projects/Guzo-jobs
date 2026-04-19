import { Filesystem, Directory } from '@capacitor/filesystem';
import { Preferences } from '@capacitor/preferences';
import type { Photo } from '@capacitor/camera';

export interface StoredPhoto {
  filepath: string;
  webviewPath?: string;
}

const PHOTO_STORAGE = 'photos';

export const convertBlobToBase64 = (blob: Blob) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => {
      resolve(String(reader.result || ''));
    };
    reader.readAsDataURL(blob);
  });

export const savePhoto = async (photo: Photo, fileName: string): Promise<StoredPhoto> => {
  const response = await fetch(photo.webPath!);
  const blob = await response.blob();
  const base64Data = await convertBlobToBase64(blob);

  const savedFile = await Filesystem.writeFile({
    path: fileName,
    data: base64Data,
    directory: Directory.Data,
  });

  return {
    filepath: savedFile.uri,
    webviewPath: photo.webPath,
  };
};

export const loadCachedPhotos = async (): Promise<StoredPhoto[]> => {
  const photoList = await Preferences.get({ key: PHOTO_STORAGE });
  const photosInPreferences: StoredPhoto[] = photoList.value ? JSON.parse(photoList.value) : [];

  for (const photo of photosInPreferences) {
    const file = await Filesystem.readFile({
      path: photo.filepath,
      directory: Directory.Data,
    });

    photo.webviewPath = `data:image/jpeg;base64,${file.data}`;
  }

  return photosInPreferences;
};

export const persistPhotos = async (photos: StoredPhoto[]) => {
  await Preferences.set({
    key: PHOTO_STORAGE,
    value: JSON.stringify(photos),
  });
};
