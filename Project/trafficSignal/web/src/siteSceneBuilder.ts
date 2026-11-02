import * as THREE from "three";
import type { SiteGeometry } from "./types";

/**
 * Builds data-driven 3D road meshes, curbs, markings, buildings, central island/fountain,
 * and labeled decorative scatter from real OpenStreetMap geometry (in metric UTM relative to site center).
 */
export function buildSiteEnvironment(
  group: THREE.Group,
  geom: SiteGeometry
): void {
  // 1. Terrain / Ground Plane
  const groundGeo = new THREE.PlaneGeometry(600, 600);
  const groundMat = new THREE.MeshStandardMaterial({
    color: 0xded9cf,
    roughness: 0.95,
    metalness: 0.02,
  });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.05;
  ground.receiveShadow = true;
  group.add(ground);

  // 2. Road Materials
  const roadMat = new THREE.MeshStandardMaterial({
    color: 0x272b2f,
    roughness: 0.86,
    metalness: 0.1,
  });
  const curbMat = new THREE.MeshStandardMaterial({
    color: 0x989fa6,
    roughness: 0.72,
    metalness: 0.05,
  });
  const lineMat = new THREE.MeshStandardMaterial({
    color: 0xf5f3ea,
    roughness: 0.45,
    metalness: 0.05,
  });

  // 3. Construct Road Ribbons from Lane Polylines
  for (const lane of geom.lanes) {
    const pts = lane.shape;
    if (pts.length < 2) continue;

    const halfWidth = (lane.width_m || 3.2) * 0.5;
    const positions: number[] = [];
    const normals: number[] = [];
    const indices: number[] = [];

    // Compute vertices along polyline
    for (let i = 0; i < pts.length; i++) {
      const p = pts[i];
      let dx = 0;
      let dy = 0;

      if (i === 0) {
        dx = pts[1][0] - p[0];
        dy = pts[1][1] - p[1];
      } else if (i === pts.length - 1) {
        dx = p[0] - pts[i - 1][0];
        dy = p[1] - pts[i - 1][1];
      } else {
        dx = pts[i + 1][0] - pts[i - 1][0];
        dy = pts[i + 1][1] - pts[i - 1][1];
      }

      const len = Math.hypot(dx, dy) || 1.0;
      // Normal vector in 2D (perpendicular to direction)
      const nx = -dy / len;
      const ny = dx / len;

      // In Three.js: X is X, Y is UP, Z is -Y (south)
      const lx = p[0] + nx * halfWidth;
      const lz = -(p[1] + ny * halfWidth);

      const rx = p[0] - nx * halfWidth;
      const rz = -(p[1] - ny * halfWidth);

      positions.push(lx, 0.02, lz);
      normals.push(0, 1, 0);

      positions.push(rx, 0.02, rz);
      normals.push(0, 1, 0);

      if (i < pts.length - 1) {
        const base = i * 2;
        indices.push(base, base + 1, base + 2);
        indices.push(base + 1, base + 3, base + 2);
      }
    }

    const roadGeo = new THREE.BufferGeometry();
    roadGeo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    roadGeo.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
    roadGeo.setIndex(indices);

    const roadMesh = new THREE.Mesh(roadGeo, roadMat);
    roadMesh.receiveShadow = true;
    group.add(roadMesh);

    // Dashed center markings along lane divider
    if (lane.index === 0) {
      for (let i = 0; i < pts.length - 1; i += 2) {
        const p1 = pts[i];
        const p2 = pts[i + 1];
        const segLen = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
        if (segLen < 1.0) continue;

        const stripeGeo = new THREE.BoxGeometry(0.18, 0.01, segLen * 0.45);
        const stripe = new THREE.Mesh(stripeGeo, lineMat);
        const mx = (p1[0] + p2[0]) * 0.5;
        const my = (p1[1] + p2[1]) * 0.5;
        stripe.position.set(mx, 0.035, -my);
        const angle = Math.atan2(p2[0] - p1[0], p2[1] - p1[1]);
        stripe.rotation.y = angle;
        group.add(stripe);
      }
    }
  }

  // 4. Extruded OSM Buildings
  const buildingMat = new THREE.MeshStandardMaterial({
    color: 0xe6e2d8,
    roughness: 0.75,
    metalness: 0.08,
  });

  for (const b of geom.buildings) {
    const pts = b.points;
    if (pts.length < 3) continue;

    const shape = new THREE.Shape();
    shape.moveTo(pts[0][0], -pts[0][1]);
    for (let i = 1; i < pts.length; i++) {
      shape.lineTo(pts[i][0], -pts[i][1]);
    }
    shape.closePath();

    const height = Math.max(4.0, b.height_m || 8.0);
    const extrudeGeo = new THREE.ExtrudeGeometry(shape, {
      depth: height,
      bevelEnabled: true,
      bevelSegments: 1,
      bevelSize: 0.15,
      bevelThickness: 0.15,
    });

    const bMesh = new THREE.Mesh(extrudeGeo, buildingMat);
    bMesh.rotation.x = Math.PI / 2;
    bMesh.position.y = height;
    bMesh.castShadow = true;
    bMesh.receiveShadow = true;
    group.add(bMesh);

    // Subtle roof border
    const roofBorderGeo = new THREE.BoxGeometry(0.3, 0.4, 0.3);
    const roofCorner = new THREE.Mesh(roofBorderGeo, curbMat);
    roofCorner.position.set(pts[0][0], height + 0.2, -pts[0][1]);
    group.add(roofCorner);
  }

  // 5. Central Island & Fountain (OSM candidate fountain at center (0, 0))
  const fountainBaseGeo = new THREE.CylinderGeometry(5.0, 5.2, 0.5, 32);
  const fountainBase = new THREE.Mesh(fountainBaseGeo, curbMat);
  fountainBase.position.set(0, 0.25, 0);
  fountainBase.receiveShadow = true;
  fountainBase.castShadow = true;
  group.add(fountainBase);

  const basinGeo = new THREE.CylinderGeometry(4.0, 4.0, 0.35, 32);
  const basinMat = new THREE.MeshStandardMaterial({
    color: 0x768087,
    roughness: 0.6,
  });
  const basin = new THREE.Mesh(basinGeo, basinMat);
  basin.position.set(0, 0.5, 0);
  group.add(basin);

  const waterGeo = new THREE.CircleGeometry(3.8, 32);
  const waterMat = new THREE.MeshStandardMaterial({
    color: 0x3d9ab0,
    roughness: 0.1,
    metalness: 0.45,
    transparent: true,
    opacity: 0.88,
  });
  const water = new THREE.Mesh(waterGeo, waterMat);
  water.rotation.x = -Math.PI / 2;
  water.position.set(0, 0.68, 0);
  group.add(water);

  const pedestalGeo = new THREE.CylinderGeometry(1.2, 1.6, 1.2, 16);
  const pedestal = new THREE.Mesh(pedestalGeo, curbMat);
  pedestal.position.set(0, 1.1, 0);
  group.add(pedestal);

  // 6. Labeled Decorative Scatter (Cosmetic trees & street lamps)
  const trunkMat = new THREE.MeshStandardMaterial({ color: 0x5a483a, roughness: 0.9 });
  const foliageMat = new THREE.MeshStandardMaterial({ color: 0x3f6e47, roughness: 0.7 });
  const lampPoleMat = new THREE.MeshStandardMaterial({ color: 0x4a535c, roughness: 0.5, metalness: 0.6 });
  const lampLightMat = new THREE.MeshStandardMaterial({
    color: 0xfff6d6,
    emissive: 0xffd982,
    emissiveIntensity: 0.7,
  });

  for (const item of geom.decorative_scatter) {
    if (item.type === "tree") {
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.28, 1.8, 8), trunkMat);
      trunk.position.set(item.x, 0.9, -item.y);
      trunk.castShadow = true;
      group.add(trunk);

      const foliage = new THREE.Mesh(new THREE.DodecahedronGeometry(1.3, 1), foliageMat);
      foliage.position.set(item.x, 2.3, -item.y);
      foliage.castShadow = true;
      group.add(foliage);
    } else {
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 4.2, 8), lampPoleMat);
      pole.position.set(item.x, 2.1, -item.y);
      pole.castShadow = true;
      group.add(pole);

      const head = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.15, 0.22), lampLightMat);
      head.position.set(item.x, 4.25, -item.y);
      group.add(head);
    }
  }
}
