import { useEffect, useRef } from "react"
import type * as THREE from "three"

type StarField = {
  renderer: THREE.WebGLRenderer
  camera: THREE.PerspectiveCamera
  scene: THREE.Scene
  geometry: THREE.BufferGeometry
  streakGeometry: THREE.BufferGeometry
  material: THREE.ShaderMaterial
  count: number
  positions: Float32Array
  sizes: Float32Array
  colors: Float32Array
  phases: Float32Array
  speeds: Float32Array
  trails: Float32Array
  streakPositions: Float32Array
  streakColors: Float32Array
}

export default function FallingStarsBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    let cancelled = false
    let cleanup: (() => void) | undefined

    void import("three").then((THREE) => {
      if (cancelled) return

      const count = window.innerWidth < 700 ? 300 : 620
      const positions = new Float32Array(count * 3)
      const sizes = new Float32Array(count)
      const colors = new Float32Array(count * 3)
      const phases = new Float32Array(count)
      const speeds = new Float32Array(count)
      const trails = new Float32Array(count)
      const streakPositions = new Float32Array(count * 6)
      const streakColors = new Float32Array(count * 6)
      const palette = [0xfff0d0, 0xffc16f, 0xff8a42, 0xff5636]
      const pointColor = new THREE.Color()
      let disposed = false

      const renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: false,
        antialias: false,
        powerPreference: "low-power",
      })
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.35))
      renderer.setSize(window.innerWidth, window.innerHeight)
      renderer.setClearColor(0x030303, 1)

      const scene = new THREE.Scene()
      scene.background = new THREE.Color(0x030303)
      const camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.1, 120)
      camera.position.z = 20
      const halfFov = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))

      const spawn = (index: number, startAbove = true) => {
        const offset = index * 3
        const depth = 8 + Math.random() * 37
        const halfHeight = depth * halfFov
        const halfWidth = halfHeight * camera.aspect
        const meteor = index % 13 === 0
        positions[offset] = (Math.random() * 2 - 1) * halfWidth
        positions[offset + 1] = startAbove
          ? halfHeight * (0.75 + Math.random() * 0.8)
          : (Math.random() * 2 - 1) * halfHeight
        positions[offset + 2] = -depth
        const paletteIndex = Math.random() < 0.42 ? 0 : Math.random() < 0.68 ? 1 : Math.random() < 0.82 ? 2 : 3
        pointColor.setHex(palette[paletteIndex])
        colors.set(pointColor.toArray(), offset)
        sizes[index] = meteor ? 2.3 + Math.random() * 2.6 : 0.58 + Math.random() * 1.55
        phases[index] = Math.random() * Math.PI * 2
        speeds[index] = meteor ? 0.25 + Math.random() * 0.3 : 0.055 + Math.random() * 0.13
        trails[index] = meteor ? 0.17 + Math.random() * 0.1 : 0.028 + Math.random() * 0.035
      }

      for (let index = 0; index < count; index += 1) spawn(index, false)

      const geometry = new THREE.BufferGeometry()
      geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3))
      geometry.setAttribute("aSize", new THREE.BufferAttribute(sizes, 1))
      geometry.setAttribute("aColor", new THREE.BufferAttribute(colors, 3))
      geometry.setAttribute("aPhase", new THREE.BufferAttribute(phases, 1))
      const material = new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          uPixelRatio: { value: renderer.getPixelRatio() },
          uTime: { value: 0 },
        },
        vertexShader: `
          attribute float aSize;
          attribute vec3 aColor;
          attribute float aPhase;
          uniform float uPixelRatio;
          uniform float uTime;
          varying vec3 vColor;
          varying float vFlicker;
          void main() {
            vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * viewPosition;
            gl_PointSize = clamp(aSize * uPixelRatio * (72.0 / -viewPosition.z), 1.2, 34.0);
            vColor = aColor;
            vFlicker = 0.68 + 0.32 * sin(uTime * 8.0 + aPhase);
          }
        `,
        fragmentShader: `
          varying vec3 vColor;
          varying float vFlicker;
          void main() {
            float radius = length(gl_PointCoord - vec2(0.5)) * 2.0;
            float halo = pow(max(0.0, 1.0 - radius), 2.2);
            float hotCore = exp(-radius * radius * 70.0);
            float alpha = (halo * 0.48 + hotCore) * vFlicker;
            gl_FragColor = vec4(vColor * (halo * 0.8 + hotCore * 1.45), alpha);
          }
        `,
      })
      scene.add(new THREE.Points(geometry, material))

      const streakGeometry = new THREE.BufferGeometry()
      streakGeometry.setAttribute("position", new THREE.BufferAttribute(streakPositions, 3))
      streakGeometry.setAttribute("color", new THREE.BufferAttribute(streakColors, 3))
      const streakMaterial = new THREE.LineBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.78,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
      scene.add(new THREE.LineSegments(streakGeometry, streakMaterial))

      const field: StarField = {
        renderer,
        camera,
        scene,
        geometry,
        streakGeometry,
        material,
        count,
        positions,
        sizes,
        colors,
        phases,
        speeds,
        trails,
        streakPositions,
        streakColors,
      }

      let frame = 0
      let previousTime = 0
      const render = (time: number) => {
        frame = requestAnimationFrame(render)
        const delta = Math.min(0.04, Math.max(0.001, (time - previousTime) / 1000))
        previousTime = time
        material.uniforms.uTime.value = time / 1000

        for (let index = 0; index < field.count; index += 1) {
          const offset = index * 3
          const depth = -field.positions[offset + 2]
          const viewHeight = depth * halfFov * 2
          field.positions[offset + 1] -= viewHeight * field.speeds[index] * delta
          field.positions[offset + 2] += (field.speeds[index] * 0.1 + 0.015) * delta

          if (field.positions[offset + 1] < -viewHeight * 0.62 || field.positions[offset + 2] > -4) {
            spawn(index)
          }

          const trailOffset = index * 6
          const trailLength = viewHeight * field.speeds[index] * field.trails[index]
          field.streakPositions[trailOffset] = field.positions[offset]
          field.streakPositions[trailOffset + 1] = field.positions[offset + 1] + trailLength
          field.streakPositions[trailOffset + 2] = field.positions[offset + 2] - 0.035
          field.streakPositions[trailOffset + 3] = field.positions[offset]
          field.streakPositions[trailOffset + 4] = field.positions[offset + 1]
          field.streakPositions[trailOffset + 5] = field.positions[offset + 2]

          for (let channel = 0; channel < 3; channel += 1) {
            const color = field.colors[offset + channel]
            field.streakColors[trailOffset + channel] = color * 0.025
            field.streakColors[trailOffset + 3 + channel] = color * 0.7
          }
        }

        field.geometry.attributes.position.needsUpdate = true
        field.streakGeometry.attributes.position.needsUpdate = true
        field.streakGeometry.attributes.color.needsUpdate = true
        renderer.render(scene, camera)
      }

      const resize = () => {
        renderer.setSize(window.innerWidth, window.innerHeight)
        camera.aspect = window.innerWidth / window.innerHeight
        camera.updateProjectionMatrix()
        material.uniforms.uPixelRatio.value = renderer.getPixelRatio()
        for (let index = 0; index < count; index += 1) spawn(index, false)
        geometry.attributes.position.needsUpdate = true
      }

      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)")
      const start = () => {
        cancelAnimationFrame(frame)
        if (reducedMotion.matches) {
          renderer.render(scene, camera)
          return
        }
        previousTime = performance.now()
        frame = requestAnimationFrame(render)
      }
      window.addEventListener("resize", resize)
      reducedMotion.addEventListener("change", start)
      start()

      cleanup = () => {
        if (disposed) return
        disposed = true
        cancelAnimationFrame(frame)
        window.removeEventListener("resize", resize)
        reducedMotion.removeEventListener("change", start)
        geometry.dispose()
        streakGeometry.dispose()
        material.dispose()
        streakMaterial.dispose()
        renderer.dispose()
      }
    })

    return () => {
      cancelled = true
      cleanup?.()
    }
  }, [])

  return <canvas ref={canvasRef} className="falling-stars-canvas" aria-hidden="true" />
}
