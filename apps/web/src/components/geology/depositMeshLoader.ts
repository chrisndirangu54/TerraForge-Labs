import {
  BoundingSphere,
  Cartesian3,
  Color,
  ColorGeometryInstanceAttribute,
  ComponentDatatype,
  Geometry,
  GeometryAttribute,
  GeometryAttributes,
  GeometryInstance,
  GeometryPipeline,
  PerInstanceColorAppearance,
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
      vertices.push([Number(parts[1]), Number(parts[2]), Number(parts[3])]);
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

  // Unindex: each triangle gets its own vertex entries so normal computation
  // works correctly without needing an index buffer on the Cesium Geometry.
  const positions = new Float64Array(indices.length * 3);
  for (let i = 0; i < indices.length; i += 1) {
    const vertex = vertices[indices[i]];
    const offset = i * 3;
    positions[offset] = vertex[0];
    positions[offset + 1] = vertex[1];
    positions[offset + 2] = vertex[2];
  }

  // Sequential index buffer matching the unindexed position array.
  const seqIndices = new Uint32Array(indices.length);
  for (let i = 0; i < indices.length; i += 1) seqIndices[i] = i;

  return { positions, indices: seqIndices };
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

  // Build geometry with only the position attribute.
  // PerInstanceColorAppearance with flat:true only requires 'position' —
  // no normals or texture coordinates — so there is no Appearance/Geometry
  // mismatch. GeometryPipeline.computeNormal is intentionally skipped
  // because flat shading does not use per-vertex normals.
  let geometry = new Geometry({
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

  // compressedAttributes are derived from the normal attribute when it exists.
  // Since we're using flat shading we compute normals only to let Cesium's
  // attribute compression pipeline produce compressedAttributes correctly.
  geometry = GeometryPipeline.computeNormal(geometry);

  const instance = new GeometryInstance({
    geometry,
    attributes: {
      color: ColorGeometryInstanceAttribute.fromColor(
        new Color(0.72, 0.55, 0.35, 0.72),
      ),
    },
  });

  // PerInstanceColorAppearance with flat:true is the correct pairing for a
  // geometry that has position + normal (after computeNormal). It avoids the
  // 'compressedAttributes' mismatch that MaterialAppearance triggers when
  // texture coordinates are absent.
  const appearance = new PerInstanceColorAppearance({
    flat: false,   // use normals for shading depth on the ore body mesh
    translucent: true,
    closed: true,
  });

  const primitive = new Primitive({
    geometryInstances: instance,
    appearance,
    asynchronous: false,
    modelMatrix,
  });

  viewer.scene.primitives.add(primitive);
  return primitive;
}