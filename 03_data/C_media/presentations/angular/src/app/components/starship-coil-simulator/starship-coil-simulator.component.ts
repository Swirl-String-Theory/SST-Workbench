import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  computed,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

const TARGET_FREQ = 130.0;
const RESONANCE_WIDTH = 15.0;
const MAX_PRESSURE = 1.7;
const PARTICLE_COUNT = 150;

@Component({
  selector: 'app-starship-coil-simulator',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './starship-coil-simulator.component.html',
  styleUrl: './starship-coil-simulator.component.css',
})
export class StarshipCoilSimulatorComponent implements AfterViewInit, OnDestroy {
  @ViewChild('canvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;

  readonly freq = signal(10);
  readonly power = signal(50);
  readonly p = signal(5);
  readonly q = signal(12);

  readonly resonanceFactor = computed(() => {
    const diff = Math.abs(this.freq() - TARGET_FREQ);
    let factor = Math.exp(-(diff * diff) / (2 * RESONANCE_WIDTH * RESONANCE_WIDTH));
    factor *= this.power() / 100;
    return factor;
  });

  readonly pressure = computed(() => this.resonanceFactor() * MAX_PRESSURE);

  readonly status = computed(() => {
    const f = this.resonanceFactor();
    if (f > 0.8) return 'CRITICAL VACUUM';
    if (f > 0.3) return 'FIELD BUILDING';
    return 'SYSTEM IDLE';
  });

  readonly isCritical = computed(() => this.resonanceFactor() > 0.8);

  private frameId?: number;
  private resizeHandler?: () => void;

  ngAfterViewInit(): void {
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let time = 0;
    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: (Math.random() - 0.5) * 2000,
      y: (Math.random() - 0.5) * 1000,
      z: (Math.random() - 0.5) * 1000,
      vx: 0,
      vy: 0,
      vz: 0,
      size: Math.random() * 2,
    }));

    const resize = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
      }
    };
    this.resizeHandler = resize;
    window.addEventListener('resize', resize);
    resize();

    const project = (x: number, y: number, z: number) => {
      const fov = 400;
      const cameraZ = 600;
      const scale = fov / (fov + z + cameraZ);
      return {
        x: canvas.width / 2 + x * scale,
        y: canvas.height / 2 + y * scale,
        scale,
      };
    };

    const rotateY = (x: number, y: number, z: number, angle: number) => {
      const cos = Math.cos(angle);
      const sin = Math.sin(angle);
      return { x: x * cos - z * sin, y, z: x * sin + z * cos };
    };

    const rotateX = (x: number, y: number, z: number, angle: number) => {
      const cos = Math.cos(angle);
      const sin = Math.sin(angle);
      return { x, y: y * cos - z * sin, z: y * sin + z * cos };
    };

    const draw = () => {
      ctx.fillStyle = 'rgba(5, 5, 5, 0.4)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const resonanceFactor = this.resonanceFactor();
      const pVal = this.p();
      const qVal = this.q();

      ctx.fillStyle = `rgba(100, 200, 255, ${0.3 + resonanceFactor})`;
      particles.forEach((pt) => {
        if (resonanceFactor > 0.1) {
          const dist = Math.sqrt(pt.x * pt.x + pt.y * pt.y + pt.z * pt.z);
          const pull = (1000 / (dist + 10)) * resonanceFactor * 5;
          pt.vx -= (pt.x / dist) * pull;
          pt.vy -= (pt.y / dist) * pull;
          pt.vz -= (pt.z / dist) * pull;
          pt.vx *= 0.95;
          pt.vy *= 0.95;
          pt.vz *= 0.95;
        } else {
          pt.vx += (Math.random() - 0.5) * 0.5;
          pt.vy += (Math.random() - 0.5) * 0.5;
          pt.vz += (Math.random() - 0.5) * 0.5;
          if (Math.abs(pt.x) > 1000) pt.vx *= -1;
          if (Math.abs(pt.y) > 500) pt.vy *= -1;
        }
        pt.x += pt.vx;
        pt.y += pt.vy;
        pt.z += pt.vz;

        let rP = rotateY(pt.x, pt.y, pt.z, time * 0.2);
        rP = rotateX(rP.x, rP.y, rP.z, time * 0.1);
        const proj = project(rP.x, rP.y, rP.z);
        if (proj.scale > 0) {
          ctx.beginPath();
          ctx.arc(proj.x, proj.y, pt.size * proj.scale, 0, Math.PI * 2);
          ctx.fill();
        }
      });

      const rVal = Math.floor(resonanceFactor * 255);
      const gVal = Math.floor(240 + resonanceFactor * 15);
      const color = `rgb(${rVal}, ${gVal}, 255)`;
      const jitter = resonanceFactor * 2;
      const R = 150;
      const r = 60;
      const steps = 600;

      ctx.beginPath();
      let firstPoint: { x: number; y: number } | null = null;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2 + resonanceFactor * 4;
      ctx.lineCap = 'round';
      ctx.shadowBlur = 10 + resonanceFactor * 40;
      ctx.shadowColor = color;

      for (let i = 0; i <= steps; i++) {
        const t = (i / steps) * Math.PI * 2;
        let kx = (R + r * Math.cos(qVal * t)) * Math.cos(pVal * t);
        let ky = (R + r * Math.cos(qVal * t)) * Math.sin(pVal * t);
        let kz = r * Math.sin(qVal * t);
        if (jitter > 0) {
          kx += (Math.random() - 0.5) * jitter;
          ky += (Math.random() - 0.5) * jitter;
          kz += (Math.random() - 0.5) * jitter;
        }
        let rot = rotateY(kx, ky, kz, time);
        rot = rotateX(rot.x, rot.y, rot.z, time * 0.5);
        const proj = project(rot.x, rot.y, rot.z);
        if (i === 0) {
          ctx.moveTo(proj.x, proj.y);
          firstPoint = proj;
        } else {
          ctx.lineTo(proj.x, proj.y);
        }
      }
      if (firstPoint) ctx.lineTo(firstPoint.x, firstPoint.y);
      ctx.stroke();
      ctx.shadowBlur = 0;

      time += 0.01 + resonanceFactor * 0.02;
      this.frameId = requestAnimationFrame(draw);
    };

    draw();
  }

  ngOnDestroy(): void {
    if (this.resizeHandler) window.removeEventListener('resize', this.resizeHandler);
    if (this.frameId) cancelAnimationFrame(this.frameId);
  }
}
