/**
 * AeroSim Photorealistic 3D Quadcopter Simulator (Three.js)
 * High-fidelity drone with carbon-fiber fuselage, brushless motors,
 * dynamic high-RPM propeller motion-blur discs, 3-axis gimbal 4K camera,
 * navigation strobe LEDs, prop-wash ground particle vortex, and realistic lighting.
 */

class Drone3DSimulator {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;

    // Drone 3D Hierarchy
    this.droneRoot = null;
    this.bodyMesh = null;
    this.gimbalGroup = null;
    this.cameraModule = null;
    this.propellers = [];
    this.blurDiscs = [];
    this.ledLights = [];
    this.beaconLed = null;

    // Particle FX
    this.dustParticles = null;

    // Camera modes: 'chase', 'fpv', 'orbit', 'top'
    this.cameraMode = 'chase';
    this.gimbalPitchDeg = -15.0;

    // Telemetry state
    this.dronePos = { x: 0, y: 0.15, z: 0 };
    this.droneRot = { roll: 0, pitch: 0, yaw: 0 };
    this.motorRpm = [0, 0, 0, 0];
    this.isArmed = false;

    this.init();
  }

  init() {
    const width = this.canvas.clientWidth || window.innerWidth;
    const height = this.canvas.clientHeight || window.innerHeight;

    // 1. Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x070b14);
    this.scene.fog = new THREE.FogExp2(0x070b14, 0.005);

    // 2. Camera
    this.camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 2000);
    this.camera.position.set(0, 4, -7);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.1;

    // 4. Orbit Controls (Three.js OrbitControls)
    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.08;
      this.controls.maxPolarAngle = Math.PI / 2 + 0.05;
      this.controls.minDistance = 1.0;
      this.controls.maxDistance = 120.0;
      this.controls.enabled = false; // Enabled in orbit mode
    }

    // 5. Lighting
    this.setupLighting();

    // 6. Environment & Helipad
    this.createEnvironment();

    // 7. Realistic 3D Drone Model
    this.createRealisticDrone();

    // 8. Prop-wash ground particle vortex
    this.createPropWashParticles();

    // Resize event
    window.addEventListener('resize', () => this.onWindowResize());

    // Animation Loop
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  setupLighting() {
    // Ambient hemispheric light (sky blue to warm ground reflection)
    const hemiLight = new THREE.HemisphereLight(0x7090b0, 0x1a2430, 0.7);
    this.scene.add(hemiLight);

    // Primary Sun Light with realistic shadow casting
    const sunLight = new THREE.DirectionalLight(0xfff6e8, 1.6);
    sunLight.position.set(40, 80, 50);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 250;
    const d = 30;
    sunLight.shadow.camera.left = -d;
    sunLight.shadow.camera.right = d;
    sunLight.shadow.camera.top = d;
    sunLight.shadow.camera.bottom = -d;
    sunLight.shadow.bias = -0.0005;
    this.scene.add(sunLight);

    // Accent Cyber Rim Light
    const rimLight = new THREE.DirectionalLight(0x00f0ff, 0.5);
    rimLight.position.set(-30, 20, -40);
    this.scene.add(rimLight);
  }

  createEnvironment() {
    // Infinite Runway Ground
    const groundGeo = new THREE.PlaneGeometry(800, 800, 64, 64);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x090e18,
      roughness: 0.88,
      metalness: 0.15,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);

    // Grid Floor
    const gridHelper = new THREE.GridHelper(800, 160, 0x00f0ff, 0x162233);
    gridHelper.position.y = 0.01;
    this.scene.add(gridHelper);

    // Helipad Landing Circle
    const padGroup = new THREE.Group();
    padGroup.position.set(0, 0.02, 0);

    // Concrete Pad Ring
    const padRingGeo = new THREE.RingGeometry(3.5, 4.2, 48);
    const padRingMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, side: THREE.DoubleSide });
    const padRing = new THREE.Mesh(padRingGeo, padRingMat);
    padRing.rotation.x = -Math.PI / 2;
    padGroup.add(padRing);

    // Inner Glowing Perimeter Ring
    const innerRingGeo = new THREE.RingGeometry(1.8, 1.95, 36);
    const innerRingMat = new THREE.MeshBasicMaterial({ color: 0xffb703, side: THREE.DoubleSide });
    const innerRing = new THREE.Mesh(innerRingGeo, innerRingMat);
    innerRing.rotation.x = -Math.PI / 2;
    padGroup.add(innerRing);

    // Helipad 'H' Marking
    const hMat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide });
    // Left vertical bar
    const h1 = new THREE.Mesh(new THREE.PlaneGeometry(0.3, 1.6), hMat);
    h1.position.set(-0.6, 0.01, 0);
    h1.rotation.x = -Math.PI / 2;
    padGroup.add(h1);
    // Right vertical bar
    const h2 = new THREE.Mesh(new THREE.PlaneGeometry(0.3, 1.6), hMat);
    h2.position.set(0.6, 0.01, 0);
    h2.rotation.x = -Math.PI / 2;
    padGroup.add(h2);
    // Cross bar
    const h3 = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.3), hMat);
    h3.position.set(0, 0.01, 0);
    h3.rotation.x = -Math.PI / 2;
    padGroup.add(h3);

    // Helipad LED Perimeter Beacon Posts
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2;
      const x = Math.cos(angle) * 4.4;
      const z = Math.sin(angle) * 4.4;
      const post = new THREE.Mesh(
        new THREE.CylinderGeometry(0.04, 0.04, 0.15, 8),
        new THREE.MeshStandardMaterial({ color: 0x222222, metalness: 0.8 })
      );
      post.position.set(x, 0.075, z);
      padGroup.add(post);

      const bulb = new THREE.Mesh(
        new THREE.SphereGeometry(0.06, 8, 8),
        new THREE.MeshBasicMaterial({ color: (i % 2 === 0) ? 0x00f0ff : 0x00ff9d })
      );
      bulb.position.set(x, 0.17, z);
      padGroup.add(bulb);
    }

    this.scene.add(padGroup);
  }

  createRealisticDrone() {
    this.droneRoot = new THREE.Group();
    this.droneRoot.position.set(0, 0.15, 0);
    this.scene.add(this.droneRoot);

    // --- High-Quality Materials ---
    // Carbon fiber composite weave for fuselage
    const carbonMat = new THREE.MeshStandardMaterial({
      color: 0x11161d,
      roughness: 0.35,
      metalness: 0.45,
    });

    // Anodized dark metal for frame and brackets
    const frameMetalMat = new THREE.MeshStandardMaterial({
      color: 0x202936,
      roughness: 0.25,
      metalness: 0.85,
    });

    // Motor Gunmetal Stator & Copper windings
    const motorStatorMat = new THREE.MeshStandardMaterial({
      color: 0x1a212d,
      roughness: 0.2,
      metalness: 0.9,
    });
    const copperCoilMat = new THREE.MeshStandardMaterial({
      color: 0xd97706,
      roughness: 0.3,
      metalness: 0.95,
    });

    // Propeller Carbon Composite
    const propMat = new THREE.MeshStandardMaterial({
      color: 0x0c1118,
      roughness: 0.3,
      metalness: 0.3,
    });

    // Propeller High-RPM Motion Blur Disc
    const blurDiscMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      depthWrite: false,
    });

    // 1. Central Aerodynamic Fuselage
    const fuselageGroup = new THREE.Group();

    // Main central pod (sleek sculpted shape)
    const bodyGeo = new THREE.CylinderGeometry(0.24, 0.29, 0.12, 16);
    bodyGeo.scale(1.2, 1.0, 1.8);
    this.bodyMesh = new THREE.Mesh(bodyGeo, carbonMat);
    this.bodyMesh.castShadow = true;
    fuselageGroup.add(this.bodyMesh);

    // Top Aero Canopy Hood
    const canopyGeo = new THREE.SphereGeometry(0.22, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2);
    canopyGeo.scale(1.0, 0.45, 1.5);
    const canopyMat = new THREE.MeshStandardMaterial({
      color: 0x090e15,
      roughness: 0.15,
      metalness: 0.6,
    });
    const canopy = new THREE.Mesh(canopyGeo, canopyMat);
    canopy.position.set(0, 0.06, 0);
    canopy.castShadow = true;
    fuselageGroup.add(canopy);

    // Top Battery Compartment & Status LED bar
    const batteryPack = new THREE.Mesh(
      new THREE.BoxGeometry(0.18, 0.08, 0.32),
      new THREE.MeshStandardMaterial({ color: 0x070b10, roughness: 0.5, metalness: 0.2 })
    );
    batteryPack.position.set(0, 0.05, -0.05);
    fuselageGroup.add(batteryPack);

    // Pulsing Central Status Beacon on Top of Canopy
    const beaconGeo = new THREE.CylinderGeometry(0.035, 0.035, 0.02, 12);
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xff3366 });
    this.beaconLed = new THREE.Mesh(beaconGeo, beaconMat);
    this.beaconLed.position.set(0, 0.14, 0.08);
    fuselageGroup.add(this.beaconLed);

    // Front Stereo Obstacle Avoidance Sensors (Dual Glass Lenses)
    for (let s of [-0.07, 0.07]) {
      const sensorBezel = new THREE.Mesh(
        new THREE.CylinderGeometry(0.025, 0.025, 0.02, 12),
        frameMetalMat
      );
      sensorBezel.rotation.x = Math.PI / 2;
      sensorBezel.position.set(s, 0.01, 0.32);
      fuselageGroup.add(sensorBezel);

      const sensorGlass = new THREE.Mesh(
        new THREE.SphereGeometry(0.018, 12, 12),
        new THREE.MeshStandardMaterial({ color: 0x00f0ff, roughness: 0.1, metalness: 0.9 })
      );
      sensorGlass.position.set(s, 0.01, 0.33);
      fuselageGroup.add(sensorGlass);
    }

    this.droneRoot.add(fuselageGroup);

    // 2. 4 Carbon Fiber Tubular Arms with Brushless Motors & Navigation Lights
    // Arms in 45-degree X configuration
    const armDistance = 0.46; // Distance from center to motor
    const armAngles = [
      Math.PI / 4,         // M1: Front-Right
      (3 * Math.PI) / 4,   // M2: Front-Left
      (5 * Math.PI) / 4,   // M3: Rear-Left
      (7 * Math.PI) / 4    // M4: Rear-Right
    ];

    const ledColors = [
      0x00ff9d, // Front Right: Aviation Green
      0xff3366, // Front Left: Aviation Red
      0xffffff, // Rear Left: White Strobe
      0xffffff  // Rear Right: White Strobe
    ];

    this.propellers = [];
    this.blurDiscs = [];
    this.ledLights = [];

    armAngles.forEach((angle, idx) => {
      const armGroup = new THREE.Group();

      const motorX = Math.cos(angle) * armDistance;
      const motorZ = Math.sin(angle) * armDistance;

      // Carbon Fiber Tube Boom
      const tubeLength = armDistance * 0.95;
      const tubeGeo = new THREE.CylinderGeometry(0.024, 0.024, tubeLength, 12);
      const tube = new THREE.Mesh(tubeGeo, carbonMat);
      tube.position.set(motorX * 0.5, 0, motorZ * 0.5);
      tube.quaternion.setFromUnitVectors(
        new THREE.Vector3(0, 1, 0),
        new THREE.Vector3(motorX, 0, motorZ).normalize()
      );
      tube.castShadow = true;
      this.droneRoot.add(tube);

      // Motor Mount Pod
      const pod = new THREE.Mesh(
        new THREE.CylinderGeometry(0.065, 0.07, 0.05, 16),
        frameMetalMat
      );
      pod.position.set(motorX, 0.02, motorZ);
      pod.castShadow = true;
      this.droneRoot.add(pod);

      // Brushless Outrunner Motor Bell
      const motorBell = new THREE.Mesh(
        new THREE.CylinderGeometry(0.055, 0.055, 0.06, 16),
        motorStatorMat
      );
      motorBell.position.set(motorX, 0.065, motorZ);
      motorBell.castShadow = true;
      this.droneRoot.add(motorBell);

      // Visible Copper Coils inside motor vents
      const copperRing = new THREE.Mesh(
        new THREE.CylinderGeometry(0.046, 0.046, 0.03, 12),
        copperCoilMat
      );
      copperRing.position.set(motorX, 0.06, motorZ);
      this.droneRoot.add(copperRing);

      // Navigation LED Strobe on underside of motor pod
      const ledGeo = new THREE.SphereGeometry(0.025, 8, 8);
      const ledMat = new THREE.MeshBasicMaterial({ color: ledColors[idx] });
      const led = new THREE.Mesh(ledGeo, ledMat);
      led.position.set(motorX, -0.015, motorZ);
      this.droneRoot.add(led);
      this.ledLights.push({ mesh: led, color: ledColors[idx], isStrobe: idx >= 2 });

      // Propeller Hub & Blades
      const propGroup = new THREE.Group();
      propGroup.position.set(motorX, 0.105, motorZ);

      // Center Nut
      const nut = new THREE.Mesh(
        new THREE.ConeGeometry(0.02, 0.03, 8),
        frameMetalMat
      );
      nut.position.y = 0.015;
      propGroup.add(nut);

      // Two Aerodynamic Curved Blades
      const bladeLength = 0.28;
      for (let b = 0; b < 2; b++) {
        const bladeGeo = new THREE.BoxGeometry(0.035, 0.005, bladeLength);
        bladeGeo.rotateY(b * Math.PI);
        const blade = new THREE.Mesh(bladeGeo, propMat);
        blade.position.set(
          Math.sin(b * Math.PI) * (bladeLength * 0.45),
          0.005,
          Math.cos(b * Math.PI) * (bladeLength * 0.45)
        );
        blade.castShadow = true;
        propGroup.add(blade);
      }

      this.droneRoot.add(propGroup);
      this.propellers.push(propGroup);

      // High-RPM Motion Blur Rotor Disc
      const discGeo = new THREE.RingGeometry(0.05, bladeLength * 0.98, 32);
      const disc = new THREE.Mesh(discGeo, blurDiscMat.clone());
      disc.rotation.x = -Math.PI / 2;
      disc.position.set(motorX, 0.11, motorZ);
      this.droneRoot.add(disc);
      this.blurDiscs.push(disc);
    });

    // 3. Shock-Absorbing Carbon Fiber Landing Legs
    for (let legAngle of [Math.PI / 3, (2 * Math.PI) / 3, (4 * Math.PI) / 3, (5 * Math.PI) / 3]) {
      const legX = Math.cos(legAngle) * 0.22;
      const legZ = Math.sin(legAngle) * 0.22;

      const legStrut = new THREE.Mesh(
        new THREE.CylinderGeometry(0.012, 0.012, 0.20, 8),
        carbonMat
      );
      legStrut.position.set(legX * 1.3, -0.06, legZ * 1.3);
      legStrut.rotation.z = Math.cos(legAngle) * 0.35;
      legStrut.rotation.x = -Math.sin(legAngle) * 0.35;
      legStrut.castShadow = true;
      this.droneRoot.add(legStrut);

      // Rubber Foot Pad
      const foot = new THREE.Mesh(
        new THREE.SphereGeometry(0.02, 8, 8),
        new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 0.9 })
      );
      foot.position.set(legX * 1.5, -0.15, legZ * 1.5);
      this.droneRoot.add(foot);
    }

    // 4. 3-Axis Stabilized 4K Gimbal Camera on the Nose
    this.gimbalGroup = new THREE.Group();
    this.gimbalGroup.position.set(0, -0.06, 0.24);

    // Gimbal Yaw Arm
    const gimbalBase = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.04, 0.03, 12),
      frameMetalMat
    );
    this.gimbalGroup.add(gimbalBase);

    // Gimbal Camera Module (pivots in pitch)
    this.cameraModule = new THREE.Group();
    this.cameraModule.position.set(0, -0.04, 0.02);

    const camHousing = new THREE.Mesh(
      new THREE.BoxGeometry(0.08, 0.07, 0.10),
      frameMetalMat
    );
    camHousing.castShadow = true;
    this.cameraModule.add(camHousing);

    // Front Optical 4K Lens with multi-coated glass reflection
    const lensBezel = new THREE.Mesh(
      new THREE.CylinderGeometry(0.03, 0.03, 0.03, 16),
      new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.9 })
    );
    lensBezel.rotation.x = Math.PI / 2;
    lensBezel.position.set(0, 0, 0.06);
    this.cameraModule.add(lensBezel);

    const lensGlass = new THREE.Mesh(
      new THREE.SphereGeometry(0.024, 16, 16),
      new THREE.MeshStandardMaterial({
        color: 0x0088ff,
        roughness: 0.05,
        metalness: 0.95,
      })
    );
    lensGlass.position.set(0, 0, 0.07);
    this.cameraModule.add(lensGlass);

    this.gimbalGroup.add(this.cameraModule);
    this.droneRoot.add(this.gimbalGroup);

    // Initial gimbal angle
    this.setGimbalPitch(this.gimbalPitchDeg);
  }

  createPropWashParticles() {
    const particleCount = 150;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const opacities = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 4;
      positions[i * 3 + 1] = 0.05 + Math.random() * 0.4;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 4;
      opacities[i] = Math.random();
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      color: 0x7799aa,
      size: 0.12,
      transparent: true,
      opacity: 0.35,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    this.dustParticles = new THREE.Points(geometry, material);
    this.scene.add(this.dustParticles);
  }

  setCameraMode(mode) {
    this.cameraMode = mode;
    if (this.controls) {
      this.controls.enabled = (mode === 'orbit');
    }
  }

  setGimbalPitch(pitchDeg) {
    this.gimbalPitchDeg = pitchDeg;
    if (this.cameraModule) {
      this.cameraModule.rotation.x = THREE.MathUtils.degToRad(pitchDeg);
    }
  }

  updateTelemetry(telem) {
    if (!telem) return;

    this.isArmed = telem.is_armed || false;

    // Position (map NED North->Z-, East->X+, Alt->Y+)
    // Note: Three.js coordinates: Y is up, X is East (right), -Z is North (forward)
    if (telem.position) {
      this.dronePos.x = telem.position.east || 0;
      this.dronePos.y = Math.max(0.15, telem.position.altitude_agl || 0.15);
      this.dronePos.z = -(telem.position.north || 0);
    }

    // Attitude (Roll, Pitch, Yaw in degrees)
    if (telem.attitude) {
      this.droneRot.roll = telem.attitude.roll || 0;
      this.droneRot.pitch = telem.attitude.pitch || 0;
      this.droneRot.yaw = telem.attitude.yaw || 0;
    }

    // Motor RPM
    if (telem.motors) {
      this.motorRpm = [
        telem.motors.m1_rpm || 0,
        telem.motors.m2_rpm || 0,
        telem.motors.m3_rpm || 0,
        telem.motors.m4_rpm || 0,
      ];
    }

    // Gimbal
    if (telem.gimbal && telem.gimbal.pitch !== undefined) {
      this.setGimbalPitch(telem.gimbal.pitch);
    }
  }

  animate() {
    requestAnimationFrame(this.animate);

    const now = performance.now() * 0.001;

    // 1. Update Drone Transform
    if (this.droneRoot) {
      // Smooth interpolation
      this.droneRoot.position.lerp(
        new THREE.Vector3(this.dronePos.x, this.dronePos.y, this.dronePos.z),
        0.35
      );

      // Orientation (Roll, Pitch, Yaw)
      const euler = new THREE.Euler(
        THREE.MathUtils.degToRad(-this.droneRot.pitch),
        THREE.MathUtils.degToRad(-this.droneRot.yaw),
        THREE.MathUtils.degToRad(this.droneRot.roll),
        'YXZ'
      );
      this.droneRoot.quaternion.slerp(new THREE.Quaternion().setFromEuler(euler), 0.35);

      // 2. Propeller Rotation & Motion Blur Discs
      const directions = [1, -1, -1, 1]; // Rotation directions
      for (let i = 0; i < this.propellers.length; i++) {
        const rpm = this.motorRpm[i] || (this.isArmed ? 2200 : 0);
        const rotSpeed = (rpm / 60) * Math.PI * 2 * 0.02 * directions[i];

        // Spin physical blade
        this.propellers[i].rotation.y += rotSpeed;

        // Dynamic motion blur disc opacity
        if (this.blurDiscs[i]) {
          const blurOpacity = THREE.MathUtils.clamp((rpm - 1200) / 4500, 0.0, 0.65);
          this.blurDiscs[i].material.opacity = blurOpacity;
        }
      }

      // 3. Strobe & Beacon LEDs
      if (this.beaconLed) {
        if (!this.isArmed) {
          // Slow pulsing red/amber when disarmed
          const pulse = (Math.sin(now * 3) + 1) * 0.5;
          this.beaconLed.material.color.setHex(pulse > 0.4 ? 0xff3366 : 0x440011);
        } else {
          // Fast tactical green flash when armed
          const flash = (Math.floor(now * 4) % 2 === 0);
          this.beaconLed.material.color.setHex(flash ? 0x00ff9d : 0x003311);
        }
      }

      // Rear Strobe Blinks
      this.ledLights.forEach((led) => {
        if (led.isStrobe) {
          const strobe = (Math.floor(now * 8) % 4 === 0);
          led.mesh.material.color.setHex(strobe ? 0xffffff : 0x222222);
        }
      });

      // 4. Prop Wash Dust Particles near ground
      if (this.dustParticles) {
        const alt = this.dronePos.y;
        if (alt < 3.0 && this.isArmed) {
          this.dustParticles.visible = true;
          this.dustParticles.position.x = this.dronePos.x;
          this.dustParticles.position.z = this.dronePos.z;
          const dustSpeed = 0.08 * (3.0 - alt);
          const pos = this.dustParticles.geometry.attributes.position.array;
          for (let i = 0; i < pos.length; i += 3) {
            pos[i] += (Math.random() - 0.5) * dustSpeed;
            pos[i + 2] += (Math.random() - 0.5) * dustSpeed;
            if (Math.abs(pos[i]) > 3.0) pos[i] = (Math.random() - 0.5) * 0.5;
            if (Math.abs(pos[i + 2]) > 3.0) pos[i + 2] = (Math.random() - 0.5) * 0.5;
          }
          this.dustParticles.geometry.attributes.position.needsUpdate = true;
        } else {
          this.dustParticles.visible = false;
        }
      }
    }

    // 5. Camera Management
    this.updateCamera();

    // 6. Render
    this.renderer.render(this.scene, this.camera);
  }

  updateCamera() {
    if (!this.droneRoot) return;

    const dronePos = this.droneRoot.position;
    const yawRad = THREE.MathUtils.degToRad(-this.droneRot.yaw);

    if (this.cameraMode === 'chase') {
      // Dynamic chase camera following behind drone
      const distance = 4.2;
      const height = 1.8;

      const targetCamX = dronePos.x - Math.sin(yawRad) * distance;
      const targetCamZ = dronePos.z - Math.cos(yawRad) * distance;
      const targetCamY = dronePos.y + height;

      this.camera.position.lerp(new THREE.Vector3(targetCamX, targetCamY, targetCamZ), 0.12);
      this.camera.lookAt(dronePos.x, dronePos.y + 0.3, dronePos.z);

    } else if (this.cameraMode === 'fpv') {
      // First Person View mounted directly in gimbal on drone nose
      const forwardDist = 0.32;
      const camY = dronePos.y + 0.02;
      const camX = dronePos.x + Math.sin(yawRad) * forwardDist;
      const camZ = dronePos.z + Math.cos(yawRad) * forwardDist;

      this.camera.position.set(camX, camY, camZ);

      // Look direction includes gimbal pitch tilt
      const lookDist = 50.0;
      const pitchRad = THREE.MathUtils.degToRad(this.gimbalPitchDeg - this.droneRot.pitch);
      const lookX = camX + Math.sin(yawRad) * Math.cos(pitchRad) * lookDist;
      const lookY = camY + Math.sin(pitchRad) * lookDist;
      const lookZ = camZ + Math.cos(yawRad) * Math.cos(pitchRad) * lookDist;

      this.camera.lookAt(lookX, lookY, lookZ);

    } else if (this.cameraMode === 'top') {
      // Nadir 90-degree satellite overhead view
      this.camera.position.set(dronePos.x, dronePos.y + 18.0, dronePos.z);
      this.camera.lookAt(dronePos.x, dronePos.y, dronePos.z);

    } else if (this.cameraMode === 'orbit') {
      if (this.controls) {
        this.controls.target.copy(dronePos);
        this.controls.update();
      }
    }
  }

  onWindowResize() {
    if (!this.canvas) return;
    const width = this.canvas.clientWidth || window.innerWidth;
    const height = this.canvas.clientHeight || window.innerHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }
}
