import {
  BoundingSphere,
  Cartesian3,
  ComponentDatatype,
  Geometry,
  GeometryAttribute,
  GeometryAttributes,
  GeometryInstance,
  Material,
  MaterialAppearance,
  Primitive,
  PrimitiveType,
  Transforms,
  type Viewer,
} from 'cesium';
import { getToken } from '../../auth/token';

type ParsedMesh = {
  positions: Float64Array;
  indices: Uint32Array;
};

export function resolveDepositMeshUrl(meshUrl: string | undefined): string | null {
  if (!meshUrl) return null;

  if (meshUrl.startsWith('/deposit/mesh')) {
    return meshUrl;
  }

  const memoryMatch = meshUrl.match(/memory:\/\/[^/]+\/models\/([^?]+)\.obj/i);
  if (memoryMatch?.[1]) {
    return `/deposit/mesh?base=${memoryMatch[1].replace(/\.obj$/i, '')}`;
  }

  const minioMatch = meshUrl.match(/models\/([^/?]+\.obj)/i);
  if (minioMatch?.[1]) {
    return `/deposit/mesh?base=${minioMatch[1].replace(/\.obj$/i, '')}`;
  }

  if (meshUrl.startsWith('http://') || meshUrl.startsWith('https://')) {
    return meshUrl;
  }

  return null;
}

function parseObj(text: string): ParsedMesh {
  const vertices: [number, number, number][] = [];
  const indices: number[] = [];

  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;

    if (line.startsWith('v ')) {
      const parts = line.split(/\s+/);
      vertices.push([
        Number(parts[1]),
        Number(parts[2]),
        Number(parts[3]),
      ]);
      continue;
    }

    if (!line.startsWith('f ')) continue;

    const faceVertices = line
      .split(/\s+/)
      .slice(1)
      .map((token) => Number(token.split('/')[0]) - 1)
      .filter((index) => Number.isFinite(index) && index >= 0);

    if (faceVertices.length < 3) continue;

    for (let i = 1; i < faceVertices.length - 1; i += 1) {
      indices.push(faceVertices[0], faceVertices[i], faceVertices[i + 1]);
    }
  }

  const positions = new Float64Array(indices.length * 3);
  for (let i = 0; i < indices.length; i += 1) {
    const vertex = vertices[indices[i]];
    const offset = i * 3;
    positions[offset] = vertex[0];
    positions[offset + 1] = vertex[1];
    positions[offset + 2] = vertex[2];
  }

  return {
    positions,
    indices: Uint32Array.from(indices.map((_, index) => index)),
  };
}

export async function loadDepositMeshPrimitive(
  viewer: Viewer,
  meshUrl: string,
  centre: { lon: number; lat: number; elevation_m?: number },
): Promise<Primitive | null> {
  const resolved = resolveDepositMeshUrl(meshUrl);
  if (!resolved) return null;

  const token = getToken();
  const response = await fetch(resolved, {
    credentials: 'include',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) {
    throw new Error(`Mesh fetch failed (${response.status})`);
  }

  const text = await response.text();
  const parsed = parseObj(text);
  if (parsed.positions.length < 9) return null;

  const origin = Cartesian3.fromDegrees(
    centre.lon,
    centre.lat,
    centre.elevation_m ?? 1180,
  );
  const modelMatrix = Transforms.eastNorthUpToFixedFrame(origin);

  const geometry = new Geometry({
    attributes: {
      position: new GeometryAttribute({
        componentDatatype: ComponentDatatype.DOUBLE,
        componentsPerAttribute: 3,
        values: parsed.positions,
      }),
    } as GeometryAttributes,
    indices: parsed.indices,
    primitiveType: PrimitiveType.TRIANGLES,
    boundingSphere: BoundingSphere.fromVertices(parsed.positions),
  });

  const primitive = new Primitive({
    geometryInstances: new GeometryInstance({ geometry }),
    appearance: new MaterialAppearance({
      material: Material.fromType('Color', {
        color: { red: 0.72, green: 0.55, blue: 0.35, alpha: 0.35 },
      }),
      translucent: true,
      closed: true,
    }),
    asynchronous: false,
    modelMatrix,
  });

  viewer.scene.primitives.add(primitive);
  return primitive;
}