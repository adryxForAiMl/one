import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { VehicleInterpolationBuffer } from "./vehicleInterpolation.js";
import { buildSiteEnvironment } from "./siteSceneBuilder";
import type { SiteGeometry } from "./types";

export type VehicleState = {
  vehicle_id: string;
  x_m: number;
  y_m: number;
  angle_degrees: number;
  speed_mps: number;
  lane_id: string;
  type_id: string;
};

export type SignalState = { phase: number; phase_state: string; green_seconds_remaining: number | null };
export type RenderQuality = "low" | "medium" | "high" | "ultra";
export type CameraPreset = "overview" | "analytic" | "street";

export type ControllerLiveState = {
  mode: string;
  vehicles: VehicleState[];
  signal: SignalState | null;
  metrics: { queues_by_approach: Record<string, number>; average_wait_seconds: number };
  decision_reason: string | null;
};

export type SceneDiagnostics = {
  renderer: { calls: number; triangles: number; points: number; lines: number; geometries: number; textures: number; programs: number | null };
  frameTimeMs: { samples: number; mean: number | null; p50: number | null; p95: number | null; p99: number | null };
  memory: { jsHeapUsedBytes: number | null; jsHeapLimitBytes: number | null };
  gpu: { vendor: string | null; renderer: string | null };
  viewport: { width: number; height: number; pixelRatio: number; resolutionScale: number };
  motion: {
    samples: number;
    meanFramePositionErrorMeters: number | null;
    p95FramePositionErrorMeters: number | null;
    trace: { simulationTimeSeconds: number; meanPositionErrorMeters: number }[];
  };
};

export type SharedTrafficRenderer = {
  renderer: THREE.WebGLRenderer;
  environment: THREE.Texture | null;
  resize: () => void;
  renderScene: (container: HTMLElement, scene: THREE.Scene, camera: THREE.Camera) => void;
  subscribe: (callback: (now: number) => void) => () => void;
  setAdaptiveResolution: (enabled: boolean) => void;
  getResolutionScale: () => number;
  recordFrameInterval: (frameIntervalMs: number) => void;
  dispose: () => void;
};

function configureRenderer(renderer: THREE.WebGLRenderer, quality: RenderQuality) {
  const pixelRatioCap = quality === "ultra" ? 2 : quality === "high" ? 1.75 : quality === "medium" ? 1.4 : 1;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, pixelRatioCap));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;
  renderer.shadowMap.enabled = quality !== "low";
  renderer.shadowMap.type = THREE.PCFShadowMap;
}

function createPbrEnvironment(renderer: THREE.WebGLRenderer) {
  const generator = new THREE.PMREMGenerator(renderer);
  const previousAutoClear = renderer.autoClear;
  const previousScissorTest = renderer.getScissorTest();
  renderer.autoClear = true;
  renderer.setScissorTest(false);
  const room = new RoomEnvironment();
  const target = generator.fromScene(room, 0.04);
  room.traverse((object) => {
    if (object instanceof THREE.Mesh || object instanceof THREE.InstancedMesh) {
      object.geometry.dispose();
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      materials.forEach((material) => material.dispose());
    }
  });
  renderer.autoClear = previousAutoClear;
  renderer.setScissorTest(previousScissorTest);
  generator.dispose();
  return target;
}

function createDynamicResolutionController(renderer: THREE.WebGLRenderer, quality: RenderQuality, getSize: () => [number, number]) {
  const pixelRatioCap = quality === "ultra" ? 2 : quality === "high" ? 1.75 : quality === "medium" ? 1.4 : 1;
  const basePixelRatio = Math.min(window.devicePixelRatio, pixelRatioCap);
  const intervals = new Float32Array(90);
  let intervalCount = 0;
  let intervalCursor = 0;
  let framesUntilEvaluation = 90;
  let stableWindows = 0;
  let enabled = false;
  let resolutionScale = 1;
  const resize = () => {
    const [width, height] = getSize();
    if (!width || !height) return;
    renderer.setPixelRatio(basePixelRatio * resolutionScale);
    renderer.setSize(width, height, false);
  };
  const setEnabled = (value: boolean) => {
    enabled = value;
    stableWindows = 0;
    intervalCount = 0;
    intervalCursor = 0;
    framesUntilEvaluation = intervals.length;
    if (!enabled && resolutionScale !== 1) {
      resolutionScale = 1;
      resize();
    }
  };
  const recordFrameInterval = (frameIntervalMs: number) => {
    if (!enabled || !Number.isFinite(frameIntervalMs) || frameIntervalMs <= 0) return;
    intervals[intervalCursor] = frameIntervalMs;
    intervalCursor = (intervalCursor + 1) % intervals.length;
    intervalCount = Math.min(intervalCount + 1, intervals.length);
    framesUntilEvaluation -= 1;
    if (framesUntilEvaluation > 0 || intervalCount < intervals.length) return;
    framesUntilEvaluation = intervals.length;
    let sum = 0;
    for (let index = 0; index < intervalCount; index += 1) sum += intervals[index];
    const meanInterval = sum / intervalCount;
    if (meanInterval > 18.2 && resolutionScale > 0.6) {
      resolutionScale = Math.max(0.6, Math.round((resolutionScale - 0.1) * 100) / 100);
      stableWindows = 0;
      resize();
    } else if (meanInterval < 16.9 && resolutionScale < 1) {
      stableWindows += 1;
      if (stableWindows >= 5) {
        resolutionScale = Math.min(1, Math.round((resolutionScale + 0.05) * 100) / 100);
        stableWindows = 0;
        resize();
      }
    } else stableWindows = 0;
  };
  resize();
  return { resize, setEnabled, getResolutionScale: () => resolutionScale, recordFrameInterval };
}

export function createSharedTrafficRenderer(root: HTMLElement, quality: RenderQuality): SharedTrafficRenderer {
  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: quality !== "low", powerPreference: "high-performance" });
  configureRenderer(renderer, quality);
  const environmentTarget = quality === "low" ? null : createPbrEnvironment(renderer);
  renderer.autoClear = false;
  renderer.info.autoReset = false;
  renderer.setScissorTest(true);
  renderer.setClearColor(0xf0eee8, 1);
  renderer.domElement.className = "shared-traffic-canvas";
  renderer.domElement.setAttribute("aria-label", "Fixed-time and adaptive live traffic intersections");
  renderer.domElement.setAttribute("role", "img");
  root.appendChild(renderer.domElement);

  const resolution = createDynamicResolutionController(renderer, quality, () => [root.clientWidth, root.clientHeight]);
  const resize = () => resolution.resize();
  const observer = new ResizeObserver(resize);
  observer.observe(root);
  resize();

  const callbacks = new Set<(now: number) => void>();
  let animationId = 0;
  let disposed = false;
  let previousFrameAt: number | null = null;
  const renderFrame = (now: number) => {
    animationId = 0;
    if (disposed) return;
    if (document.visibilityState !== "visible") return;
    if (previousFrameAt !== null) resolution.recordFrameInterval(now - previousFrameAt);
    previousFrameAt = now;
    renderer.info.reset();
    callbacks.forEach((callback) => callback(now));
    scheduleRender();
  };
  const scheduleRender = () => {
    if (!disposed && document.visibilityState === "visible" && animationId === 0) {
      animationId = requestAnimationFrame(renderFrame);
    }
  };
  const handleVisibilityChange = () => {
    if (document.visibilityState === "visible") scheduleRender();
    else {
      cancelAnimationFrame(animationId);
      animationId = 0;
    }
  };
  document.addEventListener("visibilitychange", handleVisibilityChange);
  scheduleRender();

  return {
    renderer,
    environment: environmentTarget?.texture ?? null,
    resize,
    renderScene: (container, scene, camera) => {
      const rootRect = root.getBoundingClientRect();
      const viewRect = container.getBoundingClientRect();
      const left = Math.max(0, viewRect.left - rootRect.left);
      const top = Math.max(0, viewRect.top - rootRect.top);
      const width = Math.min(viewRect.width, rootRect.width - left);
      const height = Math.min(viewRect.height, rootRect.height - top);
      if (width <= 0 || height <= 0) return;
      const bottom = rootRect.height - top - height;
      renderer.setViewport(left, bottom, width, height);
      renderer.setScissor(left, bottom, width, height);
      renderer.clear(true, true, true);
      renderer.render(scene, camera);
    },
    subscribe: (callback) => {
      callbacks.add(callback);
      return () => callbacks.delete(callback);
    },
    setAdaptiveResolution: resolution.setEnabled,
    getResolutionScale: resolution.getResolutionScale,
    recordFrameInterval: resolution.recordFrameInterval,
    dispose: () => {
      disposed = true;
      cancelAnimationFrame(animationId);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      observer.disconnect();
      callbacks.clear();
      environmentTarget?.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}

const palette = {
  asphalt: 0x454843,
  curb: 0xc9c3b7,
  sidewalk: 0xe8e4dc,
  line: 0xfaf9f5,
  yellow: 0xf4c84a,
  grass: 0xc9ddc7,
  green: 0x23834a,
  amber: 0xf59e0b,
  red: 0xdc2626,
};
const WORLD_SCALE = 0.1;

function box(scene: THREE.Object3D, size: [number, number, number], position: [number, number, number], color: number, roughness = 0.85, materialOverride?: THREE.Material) {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(...size),
    materialOverride ?? new THREE.MeshStandardMaterial({ color, roughness }),
  );
  mesh.position.set(...position);
  mesh.castShadow = false;
  mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
}

type AsphaltMaps = [THREE.Texture, THREE.Texture, THREE.Texture];

function createAsphaltMaps(): AsphaltMaps | null {
  const createCanvas = () => {
    const canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 128;
    return canvas;
  };
  const colorCanvas = createCanvas();
  const colorContext = colorCanvas.getContext("2d", { willReadFrequently: true });
  const roughnessCanvas = createCanvas();
  const roughnessContext = roughnessCanvas.getContext("2d", { willReadFrequently: true });
  const normalCanvas = createCanvas();
  const normalContext = normalCanvas.getContext("2d", { willReadFrequently: true });
  if (!colorContext || !roughnessContext || !normalContext) return null;

  const random = (() => {
    let state = 0x51a5f00d;
    return () => {
      state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
      return state / 4294967296;
    };
  })();
  const colorPixels = colorContext.createImageData(128, 128);
  const roughnessPixels = roughnessContext.createImageData(128, 128);
  const normalPixels = normalContext.createImageData(128, 128);
  for (let index = 0; index < colorPixels.data.length; index += 4) {
    const grain = Math.round((random() - 0.5) * 12);
    colorPixels.data[index] = 42 + grain;
    colorPixels.data[index + 1] = 46 + grain;
    colorPixels.data[index + 2] = 43 + grain;
    colorPixels.data[index + 3] = 255;
    const roughness = 208 + Math.round(random() * 44);
    roughnessPixels.data[index] = roughness;
    roughnessPixels.data[index + 1] = roughness;
    roughnessPixels.data[index + 2] = roughness;
    roughnessPixels.data[index + 3] = 255;
    normalPixels.data[index] = 122 + Math.round(random() * 10);
    normalPixels.data[index + 1] = 122 + Math.round(random() * 10);
    normalPixels.data[index + 2] = 253;
    normalPixels.data[index + 3] = 255;
  }
  colorContext.putImageData(colorPixels, 0, 0);
  roughnessContext.putImageData(roughnessPixels, 0, 0);
  normalContext.putImageData(normalPixels, 0, 0);
  // Two subtle tire-wear tracks break up the otherwise uniform road surface.
  colorContext.globalAlpha = 0.14;
  colorContext.fillStyle = "#262925";
  colorContext.fillRect(0, 42, 128, 4);
  colorContext.fillRect(0, 82, 128, 4);
  colorContext.globalAlpha = 1;

  const colorMap = new THREE.CanvasTexture(colorCanvas);
  colorMap.colorSpace = THREE.SRGBColorSpace;
  const roughnessMap = new THREE.CanvasTexture(roughnessCanvas);
  const normalMap = new THREE.CanvasTexture(normalCanvas);
  return [colorMap, roughnessMap, normalMap];
}

function buildRoad(scene: THREE.Object3D, ownedTextures: THREE.Texture[]) {
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(520, 520),
    new THREE.MeshStandardMaterial({ color: palette.grass, roughness: 1 }),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.24;
  ground.receiveShadow = true;
  scene.add(ground);

  const asphaltMaps = createAsphaltMaps();
  const asphaltMaterial = asphaltMaps ? (horizontal: boolean) => {
    const repeats: [number, number] = horizontal ? [13, 1.5] : [1.5, 13];
    const maps = asphaltMaps.map((texture) => {
      const tile = texture.clone();
      tile.wrapS = THREE.RepeatWrapping;
      tile.wrapT = THREE.RepeatWrapping;
      tile.repeat.set(...repeats);
      ownedTextures.push(tile);
      return tile;
    });
    return new THREE.MeshStandardMaterial({
      color: 0xffffff,
      map: maps[0] ?? null,
      roughnessMap: maps[1] ?? null,
      normalMap: maps[2] ?? null,
      roughness: 0.92,
      normalScale: new THREE.Vector2(0.22, 0.22),
    });
  } : null;
  if (asphaltMaps) ownedTextures.push(...asphaltMaps);
  box(scene, [520, 0.3, 15], [0, -0.05, 0], palette.asphalt, 0.92, asphaltMaterial?.(true));
  box(scene, [15, 0.31, 520], [0, -0.045, 0], palette.asphalt, 0.92, asphaltMaterial?.(false));

  // Raised curb and sidewalk bands border each approach.
  for (const offset of [-10, 10]) {
    box(scene, [520, 0.42, 2.2], [0, 0.12, offset], palette.curb);
    box(scene, [2.2, 0.42, 520], [offset, 0.12, 0], palette.curb);
  }
  for (const offset of [-13, 13]) {
    box(scene, [520, 0.28, 4], [0, -0.02, offset], palette.sidewalk);
    box(scene, [4, 0.28, 520], [offset, -0.02, 0], palette.sidewalk);
  }

  // Broken lane dividers, directional center lines, and stop bars.
  const lanePositions: [number, number, number, number][] = [];
  for (let distance = -245; distance < 245; distance += 12) {
    lanePositions.push([distance, 0.115, -3.7, 0], [distance, 0.115, 3.7, 0]);
    lanePositions.push([-3.7, 0.12, distance, Math.PI / 2], [3.7, 0.12, distance, Math.PI / 2]);
  }
  const laneMarks = new THREE.InstancedMesh(
    new THREE.BoxGeometry(5.5, 0.025, 0.16),
    new THREE.MeshStandardMaterial({ color: palette.line, roughness: 0.85 }),
    lanePositions.length,
  );
  const laneTransform = new THREE.Object3D();
  lanePositions.forEach(([x, y, z, rotation], index) => {
    laneTransform.position.set(x, y, z);
    laneTransform.rotation.set(0, rotation, 0);
    laneTransform.updateMatrix();
    laneMarks.setMatrixAt(index, laneTransform.matrix);
  });
  laneMarks.instanceMatrix.needsUpdate = true;
  scene.add(laneMarks);
  box(scene, [0.2, 0.03, 14.5], [0, 0.13, 0], palette.yellow);
  box(scene, [14.5, 0.03, 0.2], [0, 0.13, 0], palette.yellow);
  for (const sign of [-1, 1]) {
    box(scene, [0.42, 0.04, 14], [sign * 11.5, 0.15, 0], palette.line);
    box(scene, [14, 0.04, 0.42], [0, 0.15, sign * 11.5], palette.line);
  }

  // Zebra crossings on all four approaches.
  const crossing = new THREE.InstancedMesh(
    new THREE.BoxGeometry(0.75, 0.035, 0.82),
    new THREE.MeshStandardMaterial({ color: palette.line, roughness: 0.8 }),
    28,
  );
  let stripeIndex = 0;
  const stripeTransform = new THREE.Object3D();
  for (const side of [-1, 1]) {
    for (let stripe = -6; stripe <= 6; stripe += 2) {
      stripeTransform.position.set(side * 15, 0.16, stripe);
      stripeTransform.rotation.set(0, 0, 0);
      stripeTransform.updateMatrix();
      crossing.setMatrixAt(stripeIndex++, stripeTransform.matrix);
      stripeTransform.position.set(stripe, 0.16, side * 15);
      stripeTransform.rotation.set(0, Math.PI / 2, 0);
      stripeTransform.updateMatrix();
      crossing.setMatrixAt(stripeIndex++, stripeTransform.matrix);
    }
  }
  crossing.instanceMatrix.needsUpdate = true;
  scene.add(crossing);
  // Procedural arrows at the stop lines.
  for (const x of [-6.5, -2.2, 2.2, 6.5]) {
    const arrow = new THREE.Mesh(
      new THREE.ConeGeometry(0.43, 1.25, 3),
      new THREE.MeshStandardMaterial({ color: palette.line, roughness: 0.8 }),
    );
    arrow.rotation.x = Math.PI / 2;
    arrow.position.set(x, 0.18, -21);
    scene.add(arrow);
    const opposing = arrow.clone();
    opposing.rotation.x = -Math.PI / 2;
    opposing.position.z = 21;
    scene.add(opposing);
  }
}

function createContactShadowTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const context = canvas.getContext("2d");
  if (!context) return null;
  const gradient = context.createRadialGradient(32, 32, 3, 32, 32, 32);
  gradient.addColorStop(0, "rgba(24, 30, 22, 0.28)");
  gradient.addColorStop(0.48, "rgba(24, 30, 22, 0.16)");
  gradient.addColorStop(1, "rgba(24, 30, 22, 0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, 64, 64);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function buildBuildings(scene: THREE.Object3D) {
  const colors = [0xe5e0d6, 0xd7d2c7, 0xeeeae2, 0xded9cf, 0xcfc9bf];
  const blocks: [number, number, number, number][] = [
    [-62, -58, 25, 31], [62, -62, 29, 24], [-68, 58, 32, 28], [64, 63, 24, 34],
    [-112, -72, 35, 27], [112, -70, 28, 36], [-116, 74, 32, 26], [110, 76, 36, 29],
  ];
  const paneCount = blocks.reduce((total, _block, index) => total + (2 + (index % 4)) * 6, 0);
  const windowMaterial = new THREE.MeshStandardMaterial({ color: 0xb7b8ae, roughness: 0.4, metalness: 0.08 });
  const windows = new THREE.InstancedMesh(new THREE.BoxGeometry(1.25, 1.55, 0.08), windowMaterial, paneCount);
  const paneTransform = new THREE.Object3D();
  let paneIndex = 0;
  blocks.forEach(([x, z, width, depth], index) => {
    const floors = 2 + (index % 4);
    const height = floors * 5.5;
    const building = box(scene, [width, height, depth], [x, height / 2, z], colors[index % colors.length], 0.75);
    building.castShadow = true;
    for (let floor = 0; floor < floors; floor += 1) {
      for (const side of [-1, 1]) {
        for (let window = -1; window <= 1; window += 1) {
          paneTransform.position.set(x + window * 5, 2.2 + floor * 5.5, z + side * (depth / 2 + 0.06));
          paneTransform.updateMatrix();
          windows.setMatrixAt(paneIndex++, paneTransform.matrix);
        }
      }
    }
  });
  windows.instanceMatrix.needsUpdate = true;
  scene.add(windows);

  const trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x8b745e, roughness: 1 });
  const leafMaterial = new THREE.MeshStandardMaterial({ color: 0x5d9473, roughness: 1 });
  for (const [x, z] of [[-28, -29], [28, -29], [-29, 29], [29, 29], [-45, 34], [45, -34], [-37, -42], [40, 42]]) {
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.35, 3.4, 7), trunkMaterial);
    trunk.position.set(x, 1.7, z);
    trunk.castShadow = true;
    scene.add(trunk);
    const crown = new THREE.Mesh(new THREE.IcosahedronGeometry(1.8, 1), leafMaterial);
    crown.position.set(x, 4, z);
    crown.castShadow = true;
    scene.add(crown);
  }
}

function makeSignal(scene: THREE.Object3D, key: string, x: number, z: number) {
  const pole = new THREE.Mesh(
    new THREE.CylinderGeometry(0.16, 0.22, 5.6, 10),
    new THREE.MeshStandardMaterial({ color: 0x65645d, metalness: 0.65, roughness: 0.38 }),
  );
  pole.position.set(x, 2.8, z);
  pole.castShadow = true;
  scene.add(pole);
  const housing = new THREE.Mesh(
    new THREE.BoxGeometry(0.95, 2.2, 0.64),
    new THREE.MeshStandardMaterial({ color: 0x343631, roughness: 0.58 }),
  );
  housing.position.set(x, 5.05, z);
  scene.add(housing);
  const lights: THREE.Mesh[] = [];
  [palette.red, palette.amber, palette.green].forEach((color, index) => {
    const light = new THREE.Mesh(
      new THREE.SphereGeometry(0.29, 16, 12),
      new THREE.MeshStandardMaterial({ color: 0x45463f, emissive: 0x141510, roughness: 0.4 }),
    );
    light.position.set(x, 5.72 - index * 0.66, z + 0.34);
    scene.add(light);
    lights.push(light);
    void color;
  });
  return [key, lights] as const;
}

function vehicleSize(typeId: string): [number, number, number] {
  const type = typeId.toLowerCase();
  if (type.includes("bus")) return [2.7, 3.0, 11.5];
  if (type.includes("truck")) return [2.8, 3.1, 9.2];
  if (type.includes("van")) return [2.25, 2.4, 5.9];
  if (type.includes("suv")) return [2.15, 1.8, 5.0];
  if (type.includes("auto_rickshaw") || type.includes("autorickshaw")) return [1.3, 1.8, 2.8];
  if (type.includes("e_rickshaw") || type.includes("erickshaw")) return [1.0, 1.7, 2.6];
  if (type.includes("two_wheeler") || type.includes("motorcycle") || type.includes("bike")) return [0.75, 1.2, 1.9];
  if (type.includes("hatch")) return [1.8, 1.45, 4.2];
  return [1.9, 1.5, 4.6];
}

function colorForVehicle(id: string) {
  const cached = vehicleColorCache.get(id);
  if (cached) return cached;
  let hash = 0;
  for (let i = 0; i < id.length; i += 1) hash = (hash * 31 + id.charCodeAt(i)) | 0;
  const colors = [0x2d7548, 0x9a493c, 0x9b7b3f, 0xc8c1b4, 0x58674e, 0xc77a36, 0x713b36];
  const color = new THREE.Color(colors[Math.abs(hash) % colors.length]);
  vehicleColorCache.set(id, color);
  return color;
}

const vehicleColorCache = new Map<string, THREE.Color>();
const cabinColor = new THREE.Color(0xa9a89e);
const brakeLampBright = new THREE.Color(0xff3b30);
const brakeLampDim = new THREE.Color(0x871d18);
const wheelCorners = [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const;

function createInstances(scene: THREE.Scene, typeId: string, count: number, shadowTexture: THREE.Texture | null) {
  const dimensions = vehicleSize(typeId);
  const [physicalWidth, physicalHeight, physicalLength] = dimensions;
  const width = physicalWidth * WORLD_SCALE;
  const height = physicalHeight * WORLD_SCALE;
  const length = physicalLength * WORLD_SCALE;
  const body = new THREE.InstancedMesh(
    new RoundedBoxGeometry(width, height * 0.5, length, 2, Math.min(width, height * 0.5) * 0.13),
    new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.38, metalness: 0.16, clearcoat: 0.45 }),
    count,
  );
  const cabin = new THREE.InstancedMesh(
    new RoundedBoxGeometry(width * 0.8, height * 0.48, length * 0.48, 2, Math.min(width * 0.8, height * 0.48) * 0.18),
    new THREE.MeshPhysicalMaterial({ color: 0xc6c2b7, roughness: 0.2, metalness: 0.18, clearcoat: 0.65 }),
    count,
  );
  const wheels = new THREE.InstancedMesh(
    new THREE.CylinderGeometry(0.36 * WORLD_SCALE, 0.36 * WORLD_SCALE, 0.22 * WORLD_SCALE, 10),
    new THREE.MeshStandardMaterial({ color: 0x292a25, roughness: 0.88 }),
    count * 4,
  );
  const headlamps = new THREE.InstancedMesh(
    new THREE.BoxGeometry(width * 0.17, height * 0.1, 0.018),
    new THREE.MeshStandardMaterial({ color: 0xfff1c8, emissive: 0xffe4a0, emissiveIntensity: 0.42, roughness: 0.32 }),
    count * 2,
  );
  const taillamps = new THREE.InstancedMesh(
    new THREE.BoxGeometry(width * 0.16, height * 0.13, 0.018),
    new THREE.MeshStandardMaterial({ color: 0xff3e31, emissive: 0xef2117, emissiveIntensity: 0.55, roughness: 0.38 }),
    count * 2,
  );
  const shadows = new THREE.InstancedMesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({ map: shadowTexture, color: 0x30352b, transparent: true, depthWrite: false, toneMapped: false }),
    count,
  );
  shadows.renderOrder = 1;
  shadows.frustumCulled = false;
  headlamps.frustumCulled = false;
  taillamps.frustumCulled = false;
  body.castShadow = true;
  cabin.castShadow = true;
  wheels.castShadow = true;
  body.frustumCulled = false;
  cabin.frustumCulled = false;
  wheels.frustumCulled = false;
  scene.add(shadows, body, cabin, wheels, headlamps, taillamps);
  return { body, cabin, wheels, shadows, headlamps, taillamps, dimensions: [width, height, length] as [number, number, number] };
}

function writeVehicleInstances(
  scene: THREE.Scene,
  instances: Map<string, ReturnType<typeof createInstances>>,
  groups: Map<string, VehicleState[]>,
  vehicles: VehicleState[],
  dummy: THREE.Object3D,
  temp: THREE.Object3D,
  shadowTexture: THREE.Texture | null,
) {
  for (const group of groups.values()) group.length = 0;
  for (const vehicle of vehicles) {
    const key = vehicleSize(vehicle.type_id).join("x");
    const list = groups.get(key) ?? [];
    list.push(vehicle);
    groups.set(key, list);
  }

  for (const [key, meshes] of instances) {
    if (!groups.has(key) || groups.get(key)?.length === 0) {
      meshes.body.count = 0;
      meshes.cabin.count = 0;
      meshes.wheels.count = 0;
      meshes.shadows.count = 0;
      meshes.headlamps.count = 0;
      meshes.taillamps.count = 0;
      (meshes.body.userData.vehicleIds as string[] | undefined)?.splice(0);
    }
  }

  for (const [key, group] of groups) {
    if (!group.length) continue;
    let meshes = instances.get(key);
    if (!meshes) {
      meshes = createInstances(scene, group[0].type_id, Math.max(1, group.length), shadowTexture);
      instances.set(key, meshes);
    }
    if (meshes.body.instanceMatrix.count < group.length) {
      const capacity = Math.max(group.length, meshes.body.instanceMatrix.count * 2);
      scene.remove(meshes.body, meshes.cabin, meshes.wheels, meshes.shadows, meshes.headlamps, meshes.taillamps);
      for (const mesh of [meshes.body, meshes.cabin, meshes.wheels, meshes.shadows, meshes.headlamps, meshes.taillamps]) {
        mesh.geometry.dispose();
        const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        materials.forEach((material: THREE.Material) => material.dispose());
      }
      meshes = createInstances(scene, group[0].type_id, capacity, shadowTexture);
      instances.set(key, meshes);
    }

    const [width, height, length] = meshes.dimensions;
    const instanceIds = (meshes.body.userData.vehicleIds as string[] | undefined) ?? [];
    let colorsChanged = false;
    let brakeColorsChanged = false;
    group.forEach((vehicle, index) => {
      const yaw = Math.PI - (vehicle.angle_degrees * Math.PI) / 180;
      const sinYaw = Math.sin(yaw);
      const cosYaw = Math.cos(yaw);
      dummy.position.set(vehicle.x_m * WORLD_SCALE, height * 0.28, -vehicle.y_m * WORLD_SCALE);
      dummy.rotation.set(0, yaw, 0);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      meshes.body.setMatrixAt(index, dummy.matrix);

      const isNewVehicle = instanceIds[index] !== vehicle.vehicle_id;
      if (isNewVehicle) {
        meshes.body.setColorAt(index, colorForVehicle(vehicle.vehicle_id));
        meshes.cabin.setColorAt(index, cabinColor);
        instanceIds[index] = vehicle.vehicle_id;
        colorsChanged = true;
      }

      temp.position.set(vehicle.x_m * WORLD_SCALE, height * 0.72, -vehicle.y_m * WORLD_SCALE);
      temp.rotation.set(0, yaw, 0);
      temp.scale.set(1, 1, 1);
      temp.updateMatrix();
      meshes.cabin.setMatrixAt(index, temp.matrix);

      const wheelDistance = length * 0.31;
      const wheelWidth = width * 0.53;
      for (const [wheelIndex, [side, end]] of wheelCorners.entries()) {
        const dx = side * wheelWidth;
        const dz = end * wheelDistance;
        const localX = dx * cosYaw + dz * sinYaw;
        const localZ = -dx * sinYaw + dz * cosYaw;
        temp.position.set(vehicle.x_m * WORLD_SCALE + localX, 0.036, -vehicle.y_m * WORLD_SCALE + localZ);
        temp.rotation.set(Math.PI / 2, yaw, 0);
        temp.scale.set(1, 1, 1);
        temp.updateMatrix();
        meshes.wheels.setMatrixAt(index * 4 + wheelIndex, temp.matrix);
      }
      dummy.position.set(vehicle.x_m * WORLD_SCALE, 0.012, -vehicle.y_m * WORLD_SCALE);
      dummy.rotation.set(-Math.PI / 2, yaw, 0);
      dummy.scale.set(width * 0.76, length * 0.64, 1);
      dummy.updateMatrix();
      meshes.shadows.setMatrixAt(index, dummy.matrix);
      const isBraking = vehicle.speed_mps < 0.3;
      const previousBrakeStates = meshes.taillamps.userData.braking as boolean[] | undefined;
      const brakingStates = previousBrakeStates ?? (meshes.taillamps.userData.braking = [] as boolean[]);
      if (isNewVehicle || brakingStates[index] !== isBraking) {
        const brakeColor = isBraking ? brakeLampBright : brakeLampDim;
        meshes.taillamps.setColorAt(index * 2, brakeColor);
        meshes.taillamps.setColorAt(index * 2 + 1, brakeColor);
        brakingStates[index] = isBraking;
        brakeColorsChanged = true;
      }
      for (let lamp = 0; lamp < 2; lamp += 1) {
        const side = lamp === 0 ? -1 : 1;
        const wheelX = side * width * 0.29;
        const frontZ = length * 0.47;
        const rearZ = -length * 0.47;
        temp.rotation.set(0, yaw, 0);
        temp.scale.set(1, 1, 1);
        temp.position.set(
          vehicle.x_m * WORLD_SCALE + wheelX * cosYaw + frontZ * sinYaw,
          height * 0.36,
          -vehicle.y_m * WORLD_SCALE - wheelX * sinYaw + frontZ * cosYaw,
        );
        temp.updateMatrix();
        meshes.headlamps.setMatrixAt(index * 2 + lamp, temp.matrix);
        temp.position.set(
          vehicle.x_m * WORLD_SCALE + wheelX * cosYaw + rearZ * sinYaw,
          height * 0.36,
          -vehicle.y_m * WORLD_SCALE - wheelX * sinYaw + rearZ * cosYaw,
        );
        temp.updateMatrix();
        meshes.taillamps.setMatrixAt(index * 2 + lamp, temp.matrix);
      }
    });
    instanceIds.length = group.length;
    meshes.body.userData.vehicleIds = instanceIds;
    meshes.body.count = group.length;
    meshes.cabin.count = group.length;
    meshes.wheels.count = group.length * 4;
    meshes.shadows.count = group.length;
    meshes.headlamps.count = group.length * 2;
    meshes.taillamps.count = group.length * 2;
    meshes.body.instanceMatrix.needsUpdate = true;
    meshes.cabin.instanceMatrix.needsUpdate = true;
    meshes.wheels.instanceMatrix.needsUpdate = true;
    meshes.shadows.instanceMatrix.needsUpdate = true;
    meshes.headlamps.instanceMatrix.needsUpdate = true;
    meshes.taillamps.instanceMatrix.needsUpdate = true;
    if (brakeColorsChanged && meshes.taillamps.instanceColor) meshes.taillamps.instanceColor.needsUpdate = true;
    if (colorsChanged && meshes.body.instanceColor) meshes.body.instanceColor.needsUpdate = true;
    if (colorsChanged && meshes.cabin.instanceColor) meshes.cabin.instanceColor.needsUpdate = true;
  }
}

export function createTrafficScene(
  container: HTMLElement,
  quality: RenderQuality,
  sharedRenderer?: SharedTrafficRenderer,
  siteGeometry?: SiteGeometry | null
) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf0eee8);
  const camera = new THREE.PerspectiveCamera(43, 1, 0.1, 1200);
  camera.position.set(siteGeometry ? 14 : 5.2, siteGeometry ? 18 : 6.3, siteGeometry ? 16 : 6.8);
  const renderer = sharedRenderer?.renderer ?? new THREE.WebGLRenderer({ antialias: quality !== "low", powerPreference: "high-performance" });
  if (!sharedRenderer) {
    configureRenderer(renderer, quality);
    renderer.domElement.setAttribute("aria-label", "Live procedural 3D traffic intersection");
    renderer.domElement.setAttribute("role", "img");
    container.appendChild(renderer.domElement);
  }
  const localResolution = sharedRenderer ? null : createDynamicResolutionController(renderer, quality, () => [container.clientWidth, container.clientHeight]);
  const localEnvironmentTarget = !sharedRenderer && quality !== "low" ? createPbrEnvironment(renderer) : null;
  scene.environment = sharedRenderer?.environment ?? localEnvironmentTarget?.texture ?? null;
  scene.environmentIntensity = quality === "ultra" ? 0.5 : quality === "high" ? 0.38 : quality === "medium" ? 0.26 : 0;

  scene.add(new THREE.HemisphereLight(0xfff9ed, 0x87907c, 2.1));
  const sunlight = new THREE.DirectionalLight(0xfff4df, 3.2);
  sunlight.position.set(-15, 24, 13);
  sunlight.castShadow = quality !== "low";
  const shadowResolution = quality === "ultra" ? 4096 : quality === "high" ? 2048 : quality === "medium" ? 1024 : 512;
  sunlight.shadow.mapSize.set(shadowResolution, shadowResolution);
  const shadowBound = siteGeometry ? 35 : 16;
  sunlight.shadow.camera.left = -shadowBound;
  sunlight.shadow.camera.right = shadowBound;
  sunlight.shadow.camera.top = shadowBound;
  sunlight.shadow.camera.bottom = -shadowBound;
  sunlight.shadow.camera.near = 0.5;
  sunlight.shadow.camera.far = siteGeometry ? 90 : 56;
  sunlight.shadow.bias = -0.00035;
  sunlight.shadow.normalBias = 0.025;
  scene.add(sunlight);

  const environment = new THREE.Group();
  const ownedTextures: THREE.Texture[] = [];
  environment.scale.setScalar(WORLD_SCALE);
  let signals: Map<string, THREE.Mesh[]>;

  if (siteGeometry && siteGeometry.site_id === "boring_road_patna") {
    buildSiteEnvironment(environment, siteGeometry);
    signals = new Map([
      makeSignal(environment, "North", -12.0, -12.0),
      makeSignal(environment, "South", 12.0, 12.0),
      makeSignal(environment, "East", 12.0, -12.0),
      makeSignal(environment, "West", -12.0, 12.0),
    ]);
  } else {
    buildRoad(environment, ownedTextures);
    buildBuildings(environment);
    signals = new Map([
      makeSignal(environment, "North", -9.5, -9.5),
      makeSignal(environment, "South", 9.5, 9.5),
      makeSignal(environment, "East", 9.5, -9.5),
      makeSignal(environment, "West", -9.5, 9.5),
    ]);
  }
  scene.add(environment);
  const emptyLabel = document.createElement("div");
  emptyLabel.className = "scene-empty";
  emptyLabel.textContent = "No active vehicles reported by SUMO";
  container.appendChild(emptyLabel);
  const vehicleBuffer = new VehicleInterpolationBuffer();
  const instances = new Map<string, ReturnType<typeof createInstances>>();
  const vehicleGroups = new Map<string, VehicleState[]>();
  const dummy = new THREE.Object3D();
  const temp = new THREE.Object3D();
  const contactShadowTexture = createContactShadowTexture();
  if (contactShadowTexture) ownedTextures.push(contactShadowTexture);

  const controls = new OrbitControls(camera, sharedRenderer ? container : renderer.domElement);
  controls.target.set(0, 0, 0);
  controls.enableDamping = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  controls.dampingFactor = 0.08;
  controls.minDistance = 3;
  controls.maxDistance = siteGeometry ? 55 : 23;
  controls.maxPolarAngle = Math.PI * 0.47;
  controls.update();
  const cameraTargets: Record<CameraPreset, { position: THREE.Vector3; target: THREE.Vector3 }> = siteGeometry ? {
    overview: { position: new THREE.Vector3(14, 18, 16), target: new THREE.Vector3(0, 0, 0) },
    analytic: { position: new THREE.Vector3(0, 26, 0.01), target: new THREE.Vector3(0, 0, 0) },
    street: { position: new THREE.Vector3(2.5, 0.9, 3.2), target: new THREE.Vector3(0, 0.3, 0) },
  } : {
    overview: { position: new THREE.Vector3(5.2, 6.3, 6.8), target: new THREE.Vector3(0, 0, 0) },
    analytic: { position: new THREE.Vector3(0, 16, 0.01), target: new THREE.Vector3(0, 0, 0) },
    street: { position: new THREE.Vector3(0, 3.4, 10.5), target: new THREE.Vector3(0, 0.4, 0) },
  };
  let cameraTransition: { fromPosition: THREE.Vector3; fromTarget: THREE.Vector3; startedAt: number; preset: CameraPreset } | null = null;
  const resize = () => {
    const width = container.clientWidth;
    const height = container.clientHeight;
    if (!width || !height) return;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (sharedRenderer) sharedRenderer.resize();
    else localResolution?.resize();
  };
  const observer = new ResizeObserver(resize);
  observer.observe(container);
  resize();

  let animationId = 0;
  const frameTimes = new Float32Array(1200);
  let frameTimeCount = 0;
  let frameTimeCursor = 0;
  let previousFrameAt = performance.now();
  const motionErrors = new Float32Array(1200);
  const motionTimes = new Float64Array(1200);
  let motionSampleCount = 0;
  let motionSampleCursor = 0;
  let previousRenderTime: number | null = null;
  let previousVehicles = new Map<string, VehicleState>();
  const handleVisibilityChange = () => {
    previousFrameAt = performance.now();
    previousRenderTime = null;
    previousVehicles.clear();
    if (!sharedRenderer) {
      cancelAnimationFrame(animationId);
      animationId = 0;
      if (document.visibilityState === "visible") animationId = requestAnimationFrame(render);
    }
  };
  document.addEventListener("visibilitychange", handleVisibilityChange);
  const render = (frameTime = performance.now()) => {
    animationId = 0;
    if (document.visibilityState !== "visible") return;
    const now = frameTime;
    if (previousFrameAt > 0) {
      const frameInterval = now - previousFrameAt;
      frameTimes[frameTimeCursor] = frameInterval;
      frameTimeCursor = (frameTimeCursor + 1) % frameTimes.length;
      frameTimeCount = Math.min(frameTimeCount + 1, frameTimes.length);
      if (!sharedRenderer) localResolution?.recordFrameInterval(frameInterval);
    }
    previousFrameAt = now;
    if (cameraTransition) {
      const progress = Math.min(1, (now - cameraTransition.startedAt) / 650);
      const eased = progress * progress * (3 - 2 * progress);
      const destination = cameraTargets[cameraTransition.preset];
      camera.position.lerpVectors(cameraTransition.fromPosition, destination.position, eased);
      controls.target.lerpVectors(cameraTransition.fromTarget, destination.target, eased);
      if (progress >= 1) cameraTransition = null;
    }
    controls.update();
    const renderedState = vehicleBuffer.sample(now);
    emptyLabel.style.display = renderedState.vehicles.length ? "none" : "block";
    const recordMotion = (window as Window & { __trafficRecordMotion?: boolean }).__trafficRecordMotion === true;
    if (recordMotion && previousRenderTime !== null && renderedState.simulationTime !== null) {
      const deltaSeconds = renderedState.simulationTime - previousRenderTime;
      if (deltaSeconds > 0) {
        let totalError = 0;
        let comparableVehicles = 0;
        for (const vehicle of renderedState.vehicles) {
          const previous = previousVehicles.get(vehicle.vehicle_id);
          if (!previous) continue;
          const heading = (previous.angle_degrees * Math.PI) / 180;
          const expectedX = previous.x_m + Math.sin(heading) * previous.speed_mps * deltaSeconds;
          const expectedY = previous.y_m + Math.cos(heading) * previous.speed_mps * deltaSeconds;
          totalError += Math.hypot(vehicle.x_m - expectedX, vehicle.y_m - expectedY);
          comparableVehicles += 1;
        }
        if (comparableVehicles) {
          motionErrors[motionSampleCursor] = totalError / comparableVehicles;
          motionTimes[motionSampleCursor] = renderedState.simulationTime;
          motionSampleCursor = (motionSampleCursor + 1) % motionErrors.length;
          motionSampleCount = Math.min(motionSampleCount + 1, motionErrors.length);
        }
      }
    }
    previousRenderTime = recordMotion ? renderedState.simulationTime : null;
    previousVehicles.clear();
    if (recordMotion) {
      for (const vehicle of renderedState.vehicles) {
        previousVehicles.set(vehicle.vehicle_id, {
          vehicle_id: vehicle.vehicle_id,
          x_m: vehicle.x_m,
          y_m: vehicle.y_m,
          angle_degrees: vehicle.angle_degrees,
          speed_mps: vehicle.speed_mps,
          lane_id: vehicle.lane_id,
          type_id: vehicle.type_id,
        });
      }
    }
    writeVehicleInstances(scene, instances, vehicleGroups, renderedState.vehicles, dummy, temp, contactShadowTexture);
    if (sharedRenderer) sharedRenderer.renderScene(container, scene, camera);
    else {
      renderer.render(scene, camera);
      if (document.visibilityState === "visible") animationId = requestAnimationFrame(render);
    }
  };
  const getPerformanceSnapshot = (resetWindow = false): SceneDiagnostics => {
    if (resetWindow) {
      frameTimes.fill(0);
      frameTimeCount = 0;
      frameTimeCursor = 0;
      motionErrors.fill(0);
      motionTimes.fill(0);
      motionSampleCount = 0;
      motionSampleCursor = 0;
      previousRenderTime = null;
      previousVehicles.clear();
      previousFrameAt = performance.now();
    }
    const orderedFrames = Array.from({ length: frameTimeCount }, (_, index) =>
      frameTimes[(frameTimeCursor - frameTimeCount + index + frameTimes.length) % frameTimes.length],
    ).sort((a, b) => a - b);
    const percentile = (fraction: number) => orderedFrames.length
      ? orderedFrames[Math.min(orderedFrames.length - 1, Math.ceil(fraction * orderedFrames.length) - 1)]
      : null;
    const mean = orderedFrames.length ? orderedFrames.reduce((sum, value) => sum + value, 0) / orderedFrames.length : null;
    const orderedMotion = Array.from({ length: motionSampleCount }, (_, index) => {
      const sourceIndex = (motionSampleCursor - motionSampleCount + index + motionErrors.length) % motionErrors.length;
      return { simulationTimeSeconds: motionTimes[sourceIndex], meanPositionErrorMeters: motionErrors[sourceIndex] };
    });
    const sortedMotionErrors = orderedMotion.map((sample) => sample.meanPositionErrorMeters).sort((a, b) => a - b);
    const motionPercentile = (fraction: number) => sortedMotionErrors.length
      ? sortedMotionErrors[Math.min(sortedMotionErrors.length - 1, Math.ceil(fraction * sortedMotionErrors.length) - 1)]
      : null;
    const meanMotionError = sortedMotionErrors.length
      ? sortedMotionErrors.reduce((sum, value) => sum + value, 0) / sortedMotionErrors.length
      : null;
    const gl = renderer.getContext();
    const debugInfo = gl.getExtension("WEBGL_debug_renderer_info") as (WEBGL_debug_renderer_info & {
      UNMASKED_VENDOR_WEBGL: number;
      UNMASKED_RENDERER_WEBGL: number;
    }) | null;
    const performanceMemory = (performance as Performance & { memory?: { usedJSHeapSize?: number; jsHeapSizeLimit?: number } }).memory;
    return {
      renderer: {
        calls: renderer.info.render.calls,
        triangles: renderer.info.render.triangles,
        points: renderer.info.render.points,
        lines: renderer.info.render.lines,
        geometries: renderer.info.memory.geometries,
        textures: renderer.info.memory.textures,
        programs: renderer.info.programs?.length ?? null,
      },
      frameTimeMs: {
        samples: orderedFrames.length,
        mean,
        p50: percentile(0.50),
        p95: percentile(0.95),
        p99: percentile(0.99),
      },
      memory: {
        jsHeapUsedBytes: performanceMemory?.usedJSHeapSize ?? null,
        jsHeapLimitBytes: performanceMemory?.jsHeapSizeLimit ?? null,
      },
      gpu: debugInfo ? {
        vendor: String(gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)),
        renderer: String(gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)),
      } : { vendor: null, renderer: null },
      viewport: {
        width: sharedRenderer ? Math.round(container.clientWidth * renderer.getPixelRatio()) : renderer.domElement.width,
        height: sharedRenderer ? Math.round(container.clientHeight * renderer.getPixelRatio()) : renderer.domElement.height,
        pixelRatio: renderer.getPixelRatio(),
        resolutionScale: sharedRenderer?.getResolutionScale() ?? localResolution?.getResolutionScale() ?? 1,
      },
      motion: {
        samples: orderedMotion.length,
        meanFramePositionErrorMeters: meanMotionError,
        p95FramePositionErrorMeters: motionPercentile(0.95),
        trace: orderedMotion,
      },
    };
  };

  const update = (snapshot: ControllerLiveState | null, simulationTime: number | null, speed: number, status: string) => {
    const vehicles = snapshot?.vehicles ?? [];
    vehicleBuffer.push(simulationTime, vehicles, status, speed, performance.now());
    emptyLabel.style.display = vehicles.length ? "none" : "block";
    const phase = snapshot?.signal?.phase;
    for (const [approach, lights] of signals) {
      let active = -1;
      if ((approach === "North" || approach === "South") && phase === 0) active = 2;
      else if ((approach === "North" || approach === "South") && phase === 1) active = 1;
      else if ((approach === "East" || approach === "West") && phase === 3) active = 2;
      else if ((approach === "East" || approach === "West") && phase === 4) active = 1;
      lights.forEach((light, index) => {
        const material = light.material as THREE.MeshStandardMaterial;
        const isOn = index === active;
        const activeColor = index === 0 ? palette.red : index === 1 ? palette.amber : palette.green;
        material.color.setHex(isOn ? activeColor : 0x45463f);
        material.emissive.setHex(isOn ? activeColor : 0x111820);
      });
    }
  };
  const unsubscribeSharedRender = sharedRenderer?.subscribe(render);
  if (!sharedRenderer) render();

  return {
    update,
    getPerformanceSnapshot,
    setAdaptiveResolution: (enabled: boolean) => {
      if (sharedRenderer) sharedRenderer.setAdaptiveResolution(enabled);
      else localResolution?.setEnabled(enabled);
    },
    setCameraPreset: (preset: CameraPreset) => {
      if (cameraTransition?.preset === preset) return;
      cameraTransition = { fromPosition: camera.position.clone(), fromTarget: controls.target.clone(), startedAt: performance.now(), preset };
    },
    dispose: () => {
      cancelAnimationFrame(animationId);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      unsubscribeSharedRender?.();
      observer.disconnect();
      controls.dispose();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.InstancedMesh) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
    ownedTextures.forEach((texture) => texture.dispose());
    localEnvironmentTarget?.dispose();
      if (!sharedRenderer) {
        renderer.dispose();
        renderer.domElement.remove();
      }
      emptyLabel.remove();
    },
  };
}
