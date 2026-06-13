// @cesium/engine Math.js default-imports `mersenne-twister`; the package is CJS-only.
// Import the source file directly so this shim does not resolve back to itself via alias.
import * as MersenneTwisterModule from 'mersenne-twister/src/mersenne-twister.js';

type MersenneTwisterCtor = new (seed?: number) => {
  random(): number;
};

const MersenneTwister = (
  (MersenneTwisterModule as { default?: MersenneTwisterCtor }).default ??
  MersenneTwisterModule
) as MersenneTwisterCtor;

export default MersenneTwister;