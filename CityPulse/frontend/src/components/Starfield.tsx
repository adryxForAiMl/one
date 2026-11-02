"use client";

import { useEffect, useRef } from "react";

export default function Starfield() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let disposed = false;
    let stop: (() => void) | undefined;

    void import("three").then((THREE) => {
      if (disposed) return;

      const starCount = window.innerWidth < 720 ? 430 : 920;
      const streakCount = window.innerWidth < 720 ? 110 : 230;
      const renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: false,
        powerPreference: "low-power",
        preserveDrawingBuffer: true,
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
      renderer.setSize(window.innerWidth, window.innerHeight, false);
      renderer.setClearColor(0x020202, 0);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(64, window.innerWidth / window.innerHeight, 0.1, 300);
      const halfFov = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
      const positions = new Float32Array(starCount * 3);
      const sizes = new Float32Array(starCount);
      const colors = new Float32Array(starCount * 3);
      const alphas = new Float32Array(starCount);
      const speeds = new Float32Array(starCount);
      const streakPositions = new Float32Array(streakCount * 6);
      const streakColors = new Float32Array(streakCount * 6);
      const fireColors = [0xfff4e7, 0xffb56b, 0xff7a36, 0xff4a25];
      const temporaryColor = new THREE.Color();

      const placeStar = (index: number, z = -24 - Math.random() * 150) => {
        const depth = -z;
        const halfHeight = depth * halfFov;
        const halfWidth = halfHeight * camera.aspect;
        const offset = index * 3;
        positions[offset] = (Math.random() * 2 - 1) * halfWidth;
        positions[offset + 1] = (Math.random() * 2 - 1) * halfHeight;
        positions[offset + 2] = z;
      };

      for (let index = 0; index < starCount; index += 1) {
        const size = 0.65 + Math.random() * 1.8;
        const pick = Math.random();
        const color = fireColors[pick < 0.53 ? 0 : pick < 0.78 ? 1 : pick < 0.93 ? 2 : 3];
        temporaryColor.setHex(color);
        sizes[index] = size;
        colors.set(temporaryColor.toArray(), index * 3);
        alphas[index] = 0.38 + Math.random() * 0.62;
        speeds[index] = 0.012 + size * 0.009;
        placeStar(index);
      }

      const starGeometry = new THREE.BufferGeometry();
      starGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      starGeometry.setAttribute("aSize", new THREE.BufferAttribute(sizes, 1));
      starGeometry.setAttribute("aColor", new THREE.BufferAttribute(colors, 3));
      starGeometry.setAttribute("aAlpha", new THREE.BufferAttribute(alphas, 1));

      const starMaterial = new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: { uPixelRatio: { value: renderer.getPixelRatio() } },
        vertexShader: `
          attribute float aSize;
          attribute vec3 aColor;
          attribute float aAlpha;
          uniform float uPixelRatio;
          varying vec3 vColor;
          varying float vAlpha;
          void main() {
            vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * viewPosition;
            gl_PointSize = clamp(aSize * uPixelRatio * (250.0 / -viewPosition.z), 1.0, 28.0);
            vColor = aColor;
            vAlpha = aAlpha;
          }
        `,
        fragmentShader: `
          varying vec3 vColor;
          varying float vAlpha;
          void main() {
            float radius = length(gl_PointCoord - vec2(0.5)) * 2.0;
            float halo = pow(max(0.0, 1.0 - radius), 3.0);
            float hotCore = exp(-radius * radius * 75.0);
            float alpha = (halo * 0.42 + hotCore) * vAlpha;
            gl_FragColor = vec4(vColor * (halo * 0.72 + hotCore * 1.6), alpha);
          }
        `,
      });
      scene.add(new THREE.Points(starGeometry, starMaterial));

      const streakGeometry = new THREE.BufferGeometry();
      streakGeometry.setAttribute("position", new THREE.BufferAttribute(streakPositions, 3));
      streakGeometry.setAttribute("color", new THREE.BufferAttribute(streakColors, 3));
      const streakMaterial = new THREE.LineBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.7,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      scene.add(new THREE.LineSegments(streakGeometry, streakMaterial));

      const updateStreaks = () => {
        for (let index = 0; index < streakCount; index += 1) {
          const starOffset = index * 3;
          const lineOffset = index * 6;
          const x = positions[starOffset];
          const y = positions[starOffset + 1];
          const z = positions[starOffset + 2];
          const depth = -z;
          const trail = depth * (0.007 + speeds[index] * 0.018);
          streakPositions[lineOffset] = x;
          streakPositions[lineOffset + 1] = y + trail;
          streakPositions[lineOffset + 2] = z - depth * 0.018;
          streakPositions[lineOffset + 3] = x;
          streakPositions[lineOffset + 4] = y;
          streakPositions[lineOffset + 5] = z;
          const colorOffset = index * 3;
          for (let channel = 0; channel < 3; channel += 1) {
            const color = colors[colorOffset + channel];
            streakColors[lineOffset + channel] = color * 0.06;
            streakColors[lineOffset + 3 + channel] = color * 0.72;
          }
        }
        streakGeometry.attributes.position.needsUpdate = true;
        streakGeometry.attributes.color.needsUpdate = true;
      };

      const resize = () => {
        renderer.setSize(window.innerWidth, window.innerHeight, false);
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        starMaterial.uniforms.uPixelRatio.value = renderer.getPixelRatio();
      };

      let animationFrame = 0;
      let lastFrame = 0;
      const render = (time: number) => {
        animationFrame = requestAnimationFrame(render);
        const delta = Math.min(0.035, Math.max(0.001, (time - lastFrame) / 1000));
        lastFrame = time;
        const frameScale = delta * 60;

        for (let index = 0; index < starCount; index += 1) {
          const offset = index * 3;
          const depth = -positions[offset + 2];
          positions[offset + 1] -= depth * 0.0038 * frameScale;
          positions[offset + 2] += speeds[index] * frameScale;
          if (positions[offset + 2] > -3 || positions[offset + 1] < -depth * halfFov * 1.12) {
            placeStar(index);
          }
        }

        starGeometry.attributes.position.needsUpdate = true;
        updateStreaks();
        renderer.render(scene, camera);
      };

      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
      const start = () => {
        cancelAnimationFrame(animationFrame);
        if (reducedMotion.matches) {
          updateStreaks();
          renderer.render(scene, camera);
        } else {
          lastFrame = performance.now();
          animationFrame = requestAnimationFrame(render);
        }
      };
      window.addEventListener("resize", resize);
      reducedMotion.addEventListener("change", start);
      start();

      stop = () => {
        cancelAnimationFrame(animationFrame);
        window.removeEventListener("resize", resize);
        reducedMotion.removeEventListener("change", start);
        starGeometry.dispose();
        starMaterial.dispose();
        streakGeometry.dispose();
        streakMaterial.dispose();
        renderer.dispose();
      };
    });

    return () => {
      disposed = true;
      stop?.();
    };
  }, []);

  return <canvas ref={canvasRef} className="starfield-canvas" aria-hidden="true" />;
}