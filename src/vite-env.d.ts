/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_FRONT_API: string;
  // add other variables here
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

