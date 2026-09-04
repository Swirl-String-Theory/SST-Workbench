import React, { useEffect, useRef, useState } from 'react';
import './StarshipCoilSimulator.css';

export const StarshipCoilSimulator: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [freq, setFreq] = useState(10);
    const [power, setPower] = useState(50);
    const [p, setP] = useState(5);
    const [q, setQ] = useState(12);
    const [pressure, setPressure] = useState(0);
    const [status, setStatus] = useState("SYSTEM IDLE");
    const [isCritical, setIsCritical] = useState(false);

    // Physics Constants
    const TARGET_FREQ = 130.0;
    const RESONANCE_WIDTH = 15.0;
    const MAX_PRESSURE = 1.7;
    const PARTICLE_COUNT = 150;

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationFrameId: number;
        let time = 0;
        
        // Initialize Particles
        const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
            x: (Math.random() - 0.5) * 2000,
            y: (Math.random() - 0.5) * 1000,
            z: (Math.random() - 0.5) * 1000,
            vx: 0, vy: 0, vz: 0,
            size: Math.random() * 2
        }));

        const resize = () => {
            if (canvas.parentElement) {
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;
            }
        };
        window.addEventListener('resize', resize);
        resize();

        const project = (x: number, y: number, z: number) => {
            const fov = 400;
            const cameraZ = 600;
            const scale = fov / (fov + z + cameraZ);
            return {
                x: canvas.width / 2 + x * scale,
                y: canvas.height / 2 + y * scale,
                scale: scale
            };
        };

        const rotateY = (x: number, y: number, z: number, angle: number) => {
            const cos = Math.cos(angle);
            const sin = Math.sin(angle);
            return {
                x: x * cos - z * sin,
                y: y,
                z: x * sin + z * cos
            };
        };

        const rotateX = (x: number, y: number, z: number, angle: number) => {
            const cos = Math.cos(angle);
            const sin = Math.sin(angle);
            return {
                x: x,
                y: y * cos - z * sin,
                z: y * sin + z * cos
            };
        };

        const calculateResonance = () => {
            const diff = Math.abs(freq - TARGET_FREQ);
            let factor = Math.exp(-(diff * diff) / (2 * (RESONANCE_WIDTH * RESONANCE_WIDTH)));
            factor *= (power / 100);
            return factor;
        };

        const draw = () => {
            ctx.fillStyle = 'rgba(5, 5, 5, 0.4)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const resonanceFactor = calculateResonance();
            const currentPressure = resonanceFactor * MAX_PRESSURE;
            
            // Update state for UI (throttled slightly in a real app, but here we just update refs/vars usually)
            // For React state updates inside RAF, we need to be careful. 
            // We'll update the pressure state outside the loop or use refs for performance if needed.
            // But for this demo, let's just update the visual elements directly via React state in a useEffect
            // or just let the canvas handle the visuals and React handle the controls.
            
            // Draw Particles
            ctx.fillStyle = `rgba(100, 200, 255, ${0.3 + resonanceFactor})`;
            
            particles.forEach(pt => {
                if (resonanceFactor > 0.1) {
                    const dist = Math.sqrt(pt.x*pt.x + pt.y*pt.y + pt.z*pt.z);
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
                    if(Math.abs(pt.x) > 1000) pt.vx *= -1;
                    if(Math.abs(pt.y) > 500) pt.vy *= -1;
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

            // Draw Coil
            ctx.beginPath();
            const steps = 600;
            let firstPoint = null;

            const rVal = Math.floor(resonanceFactor * 255);
            const gVal = Math.floor(240 + resonanceFactor * 15);
            const bVal = 255;
            const color = `rgb(${rVal}, ${gVal}, ${bVal})`;
            
            ctx.strokeStyle = color;
            ctx.lineWidth = 2 + (resonanceFactor * 4);
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            
            ctx.shadowBlur = 10 + (resonanceFactor * 40);
            ctx.shadowColor = color;

            const jitter = resonanceFactor * 2;
            const R = 150;
            const r = 60;

            for (let i = 0; i <= steps; i++) {
                const t = (i / steps) * Math.PI * 2;
                
                let kx = (R + r * Math.cos(q * t)) * Math.cos(p * t);
                let ky = (R + r * Math.cos(q * t)) * Math.sin(p * t);
                let kz = r * Math.sin(q * t);

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

            // Ghost Coil
            ctx.beginPath();
            ctx.strokeStyle = `rgba(${rVal}, ${gVal}, ${bVal}, 0.3)`;
            ctx.lineWidth = 1;
            
            for (let i = 0; i <= steps; i++) {
                const t = (i / steps) * Math.PI * 2;
                const t2 = t + 0.05; 
                
                let kx = (R + r * Math.cos(q * t2)) * Math.cos(p * t2);
                let ky = (R + r * Math.cos(q * t2)) * Math.sin(p * t2);
                let kz = r * Math.sin(q * t2);

                let rot = rotateY(kx, ky, kz, time);
                rot = rotateX(rot.x, rot.y, rot.z, time * 0.5);
                const proj = project(rot.x, rot.y, rot.z);
                if (i === 0) ctx.moveTo(proj.x, proj.y);
                else ctx.lineTo(proj.x, proj.y);
            }
            ctx.stroke();

            time += 0.01 + (resonanceFactor * 0.02);
            animationFrameId = requestAnimationFrame(draw);
        };

        draw();

        return () => {
            window.removeEventListener('resize', resize);
            cancelAnimationFrame(animationFrameId);
        };
    }, [freq, power, p, q]);

    // Update status effect separately to avoid re-running canvas init
    useEffect(() => {
        const diff = Math.abs(freq - TARGET_FREQ);
        let factor = Math.exp(-(diff * diff) / (2 * (RESONANCE_WIDTH * RESONANCE_WIDTH)));
        factor *= (power / 100);
        
        setPressure(factor * MAX_PRESSURE);

        if (factor > 0.8) {
            setStatus("CRITICAL VACUUM");
            setIsCritical(true);
        } else if (factor > 0.3) {
            setStatus("FIELD BUILDING");
            setIsCritical(false);
        } else {
            setStatus("SYSTEM IDLE");
            setIsCritical(false);
        }
    }, [freq, power]);

    return (
        <div className="coil-container">
            <div className="coil-header">
                <div>
                    <h1 className="coil-h1">SST Starship Coil</h1>
                    <div style={{ fontSize: '0.7rem', color: '#666' }}>Topological Vorticity Confinement System</div>
                </div>
                <div className={`coil-status-badge ${isCritical || status === "FIELD BUILDING" ? 'active' : ''}`} style={{ color: isCritical ? '#00f0ff' : (status === "SYSTEM IDLE" ? '#666' : '#fff') }}>
                    {status}
                </div>
            </div>

            <div className="coil-main">
                <div className="coil-canvas-container">
                    <div className="coil-hud"></div>
                    <canvas ref={canvasRef} className="coil-canvas"></canvas>
                </div>

                <aside className="coil-aside">
                    <div className="coil-control-group">
                        <h3>Resonance Tuner</h3>
                        <label className="coil-label">Drive Frequency <span>{freq.toFixed(1)} kHz</span></label>
                        <input 
                            type="range" 
                            className="coil-range"
                            min="0" 
                            max="200" 
                            value={freq} 
                            step="0.1" 
                            onChange={(e) => setFreq(parseFloat(e.target.value))}
                        />
                        
                        <label className="coil-label">Input Power <span>{power}%</span></label>
                        <input 
                            type="range" 
                            className="coil-range"
                            min="0" 
                            max="100" 
                            value={power} 
                            onChange={(e) => setPower(parseInt(e.target.value))}
                        />

                        <div className="coil-readout">
                            <span>{pressure.toFixed(2)}</span>
                            <span className="unit" style={{ fontSize: '0.8rem', color: '#666', marginLeft: '5px' }}>MPa (Vacuum Stress)</span>
                        </div>
                        <div className={`coil-warning ${isCritical ? 'visible' : ''}`}>⚠️ RESONANCE LOCK ⚠️</div>
                    </div>

                    <div className="coil-control-group">
                        <h3>Coil Geometry (p, q)</h3>
                        <label className="coil-label">Poloidal Winding (p) <span>{p}</span></label>
                        <input 
                            type="range" 
                            className="coil-range"
                            min="2" 
                            max="10" 
                            value={p} 
                            step="1" 
                            onChange={(e) => setP(parseInt(e.target.value))}
                        />
                        <label className="coil-label">Toroidal Winding (q) <span>{q}</span></label>
                        <input 
                            type="range" 
                            className="coil-range"
                            min="2" 
                            max="20" 
                            value={q} 
                            step="1" 
                            onChange={(e) => setQ(parseInt(e.target.value))}
                        />
                        <div style={{ fontSize: '0.7rem', color: '#666' }}>Standard Starship Config: (5, 12)</div>
                    </div>

                    <div className="coil-control-group">
                        <h3>SST Theory</h3>
                        <div className="coil-analogy-box">
                            "Imagine a swimming pool. Spin a rope in a knot. At the right rhythm, the water creates a 'hole' in pressure. This device pulls the vacuum itself."
                        </div>
                    </div>
                </aside>
            </div>
        </div>
    );
};
