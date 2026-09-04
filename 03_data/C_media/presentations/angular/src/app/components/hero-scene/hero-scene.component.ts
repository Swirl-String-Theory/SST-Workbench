import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
} from '@angular/core';
import * as THREE from 'three';

@Component({
  selector: 'app-hero-scene',
  standalone: true,
  template: `
    <div class="absolute inset-0 z-0 pointer-events-none">
      <canvas #canvas class="w-full h-full block"></canvas>
    </div>
  `,
})
export class HeroSceneComponent implements AfterViewInit, OnDestroy {
  @ViewChild('canvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;

  private renderer?: THREE.WebGLRenderer;
  private scene?: THREE.Scene;
  private camera?: THREE.PerspectiveCamera;
  private torus?: THREE.Mesh;
  private particles: THREE.Mesh[] = [];
  private particleBase: THREE.Vector3[] = [];
  private frameId?: number;
  private clock = new THREE.Clock();
  private resizeHandler?: () => void;

  ngAfterViewInit(): void {
    const canvas = this.canvasRef.nativeElement;
    const parent = canvas.parentElement;
    if (!parent) return;

    const w = parent.clientWidth;
    const h = parent.clientHeight;

    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.Fog('#020617', 5, 20);

    this.camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    this.camera.position.z = 8;

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    this.scene.add(new THREE.AmbientLight(0xffffff, 0.2));
    const cyanLight = new THREE.PointLight(0x22d3ee, 1.5);
    cyanLight.position.set(10, 10, 10);
    this.scene.add(cyanLight);
    const purpleLight = new THREE.PointLight(0xc084fc, 0.5);
    purpleLight.position.set(-10, -10, -10);
    this.scene.add(purpleLight);

    const torusGeo = new THREE.TorusGeometry(2.5, 0.4, 32, 64);
    const torusMat = new THREE.MeshStandardMaterial({
      color: 0x22d3ee,
      emissive: 0x0891b2,
      emissiveIntensity: 0.5,
      transparent: true,
      opacity: 0.6,
      metalness: 1,
      roughness: 0,
    });
    this.torus = new THREE.Mesh(torusGeo, torusMat);
    this.torus.rotation.x = Math.PI / 3;
    this.scene.add(this.torus);

    const wireGeo = new THREE.TorusGeometry(2.5, 0.41, 16, 50);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x22d3ee,
      wireframe: true,
      transparent: true,
      opacity: 0.1,
    });
    const wire = new THREE.Mesh(wireGeo, wireMat);
    wire.rotation.x = Math.PI / 3;
    this.scene.add(wire);

    const sphereGeo = new THREE.SphereGeometry(0.08, 12, 12);
    for (let i = 0; i < 40; i++) {
      const color = Math.random() > 0.5 ? 0x22d3ee : 0xc084fc;
      const mat = new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 2,
        roughness: 0.1,
      });
      const mesh = new THREE.Mesh(sphereGeo, mat);
      const base = new THREE.Vector3(
        (Math.random() - 0.5) * 15,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 8,
      );
      mesh.position.copy(base);
      mesh.scale.setScalar(Math.random() * 0.5 + 0.2);
      this.particles.push(mesh);
      this.particleBase.push(base);
      this.scene.add(mesh);
    }

    const starsGeo = new THREE.BufferGeometry();
    const starCount = 800;
    const positions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i++) {
      positions[i] = (Math.random() - 0.5) * 80;
    }
    starsGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const stars = new THREE.Points(
      starsGeo,
      new THREE.PointsMaterial({ color: 0xfbbf24, size: 0.05, transparent: true, opacity: 0.6 }),
    );
    this.scene.add(stars);

    this.resizeHandler = () => {
      const pw = parent.clientWidth;
      const ph = parent.clientHeight;
      this.camera!.aspect = pw / ph;
      this.camera!.updateProjectionMatrix();
      this.renderer!.setSize(pw, ph);
    };
    window.addEventListener('resize', this.resizeHandler);

    const animate = () => {
      const t = this.clock.getElapsedTime();
      if (this.torus) {
        this.torus.rotation.x = Math.PI / 3 + t * 0.2;
        this.torus.rotation.y = t * 0.1;
      }
      this.particles.forEach((mesh, i) => {
        const base = this.particleBase[i];
        const r = Math.sqrt(base.x * base.x + base.z * base.z);
        const angle = Math.atan2(base.z, base.x) + t * 0.5;
        mesh.position.x = r * Math.cos(angle);
        mesh.position.z = r * Math.sin(angle);
        mesh.position.y = base.y + Math.sin(t * 3 + base.x) * 0.1;
      });
      this.renderer!.render(this.scene!, this.camera!);
      this.frameId = requestAnimationFrame(animate);
    };
    animate();
  }

  ngOnDestroy(): void {
    if (this.resizeHandler) window.removeEventListener('resize', this.resizeHandler);
    if (this.frameId) cancelAnimationFrame(this.frameId);
    this.renderer?.dispose();
  }
}
