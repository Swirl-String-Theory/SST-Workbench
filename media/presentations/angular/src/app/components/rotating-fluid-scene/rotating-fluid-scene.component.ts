import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
} from '@angular/core';
import * as THREE from 'three';

@Component({
  selector: 'app-rotating-fluid-scene',
  standalone: true,
  template: `
    <div class="w-full h-full absolute inset-0">
      <canvas #canvas class="w-full h-full block"></canvas>
    </div>
  `,
})
export class RotatingFluidSceneComponent implements AfterViewInit, OnDestroy {
  @ViewChild('canvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;

  private renderer?: THREE.WebGLRenderer;
  private scene?: THREE.Scene;
  private camera?: THREE.PerspectiveCamera;
  private group?: THREE.Group;
  private particles: THREE.Mesh[] = [];
  private particleBase: { r: number; theta: number; y: number }[] = [];
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
    this.scene.background = new THREE.Color('#0f172a');

    this.camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    this.camera.position.set(0, 2, 5);

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    this.scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const spot = new THREE.SpotLight(0x22d3ee, 2);
    spot.position.set(5, 10, 5);
    this.scene.add(spot);
    const point = new THREE.PointLight(0xfbbf24, 1);
    point.position.set(-2, 2, 2);
    this.scene.add(point);

    this.group = new THREE.Group();
    this.group.position.y = -1;

    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0x94a3b8,
      transmission: 0.95,
      transparent: true,
      roughness: 0,
      ior: 1.5,
      thickness: 0.5,
      clearcoat: 1,
    });
    const container = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.5, 3, 32), glassMat);
    container.position.y = 1.5;
    this.group.add(container);

    const fluid = new THREE.Mesh(
      new THREE.CylinderGeometry(1.45, 1.45, 2, 32),
      new THREE.MeshStandardMaterial({
        color: 0x0891b2,
        transparent: true,
        opacity: 0.4,
        emissive: 0x0891b2,
        emissiveIntensity: 0.2,
      }),
    );
    fluid.position.y = 1;
    this.group.add(fluid);

    const axis = new THREE.Mesh(
      new THREE.CylinderGeometry(0.05, 0.05, 3.5, 16),
      new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.9, roughness: 0.1 }),
    );
    axis.position.y = 1.75;
    this.group.add(axis);

    const base = new THREE.Mesh(
      new THREE.CylinderGeometry(1.8, 1.8, 0.2, 32),
      new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 }),
    );
    this.group.add(base);

    const sphereGeo = new THREE.SphereGeometry(0.08, 8, 8);
    for (let i = 0; i < 50; i++) {
      const r = 0.5 + Math.random() * 0.8;
      const theta = Math.random() * Math.PI * 2;
      const y = 0.5 + Math.random() * 2;
      const col = i % 2 === 0 ? 0xfbbf24 : 0x22d3ee;
      const mesh = new THREE.Mesh(
        sphereGeo,
        new THREE.MeshStandardMaterial({ color: col, emissive: col, emissiveIntensity: 1 }),
      );
      mesh.position.set(r * Math.cos(theta), y, r * Math.sin(theta));
      mesh.scale.setScalar(0.4);
      this.particles.push(mesh);
      this.particleBase.push({ r, theta, y });
      this.group.add(mesh);
    }

    this.scene.add(this.group);

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
      if (this.group) this.group.rotation.y = t * 0.15;
      this.particles.forEach((mesh, i) => {
        const b = this.particleBase[i];
        const angle = b.theta + t * 0.8;
        mesh.position.x = b.r * Math.cos(angle);
        mesh.position.z = b.r * Math.sin(angle);
        mesh.position.y = b.y + Math.sin(t * 2 + i) * 0.05;
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
