/// <reference types="vite/client" />

declare module 'mersenne-twister/src/mersenne-twister.js' {
  type MersenneTwisterCtor = new (seed?: number) => {
    random(): number;
  };

  const MersenneTwister: MersenneTwisterCtor;
  export default MersenneTwister;
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}