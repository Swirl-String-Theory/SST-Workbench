/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/

import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, MeshDistortMaterial, Sphere, Torus, Cylinder, Stars, Environment, Sparkles } from '@react-three/drei';
import * as THREE from 'three';

declare global {
  namespace JSX {
    interface IntrinsicElements {
      meshStandardMaterial: any;
      group: any;
      meshBasicMaterial: any;
      fog: any;
      ambientLight: any;
      pointLight: any;
      color: any;
      spotLight: any;
      meshPhysicalMaterial: any;
    }
  }
}

const FluidParticle = ({ position, color, scale = 1 }: { position: [number, number, number]; color: string; scale?: number }) => {
  const ref = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.getElapsedTime();
      // Swirling motion
      const r = Math.sqrt(position[0]*position[0] + position[2]*position[2]);
      const angle = Math.atan2(position[2], position[0]) + t * 0.5;
      ref.current.position.x = r * Math.cos(angle);
      ref.current.position.z = r * Math.sin(angle);
      ref.current.position.y = position[1] + Math.sin(t * 3 + position[0]) * 0.1;
    }
  });

  return (
    <Sphere ref={ref} args={[0.08, 16, 16]} position={position} scale={scale}>
      <meshStandardMaterial 
        color={color} 
        emissive={color}
        emissiveIntensity={2}
        roughness={0.1} 
        toneMapped={false}
      />
    </Sphere>
  );
};

const VortexRing = () => {
  const ref = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (ref.current) {
       const t = state.clock.getElapsedTime();
       // Rolling motion of a vortex ring
       ref.current.rotation.x = t * 0.2; 
       ref.current.rotation.y = t * 0.1;
    }
  });

  return (
    <group>
        <Torus ref={ref} args={[2.5, 0.4, 64, 100]} rotation={[Math.PI / 3, 0, 0]}>
        <MeshDistortMaterial 
            color="#22d3ee" // Cyan
            emissive="#0891b2" // Cyan 600
            emissiveIntensity={0.5} 
            transparent 
            opacity={0.6} 
            distort={0.4} 
            speed={2}
            roughness={0}
            metalness={1}
            wireframe={false}
        />
        </Torus>
        {/* Wireframe overlay for technical look */}
        <Torus args={[2.5, 0.41, 16, 50]} rotation={[Math.PI / 3, 0, 0]}>
             <meshBasicMaterial color="#22d3ee" wireframe transparent opacity={0.1} />
        </Torus>
    </group>
  );
}

export const HeroScene: React.FC = () => {
  return (
    <div className="absolute inset-0 z-0 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
        <fog attach="fog" args={['#020617', 5, 20]} />
        <ambientLight intensity={0.2} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#22d3ee" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#c084fc" />
        
        <Float speed={1} rotationIntensity={0.2} floatIntensity={0.5}>
          <VortexRing />
        </Float>
        
        {/* Ambient particles representing fluid medium */}
        <group>
            {[...Array(40)].map((_, i) => {
                const x = (Math.random() - 0.5) * 15;
                const y = (Math.random() - 0.5) * 10;
                const z = (Math.random() - 0.5) * 8;
                return <FluidParticle key={i} position={[x, y, z]} color={Math.random() > 0.5 ? "#22d3ee" : "#c084fc"} scale={Math.random() * 0.5 + 0.2} />
            })}
        </group>

        <Sparkles count={50} scale={10} size={2} speed={0.4} opacity={0.5} color="#fbbf24" />
        <Stars radius={100} depth={50} count={3000} factor={4} saturation={1} fade speed={1} />
      </Canvas>
    </div>
  );
};

export const RotatingFluidScene: React.FC = () => {
  return (
    <div className="w-full h-full absolute inset-0">
      <Canvas camera={{ position: [0, 2, 5], fov: 45 }}>
        <color attach="background" args={['#0f172a']} />
        <ambientLight intensity={0.5} />
        <spotLight position={[5, 10, 5]} angle={0.3} penumbra={1} intensity={2} color="#22d3ee" />
        <pointLight position={[-2, 2, 2]} intensity={1} color="#fbbf24" />
        <Environment preset="city" />
        
        <group position={[0, -1, 0]}>
            {/* The Rotating Cylinder (Container) */}
            <Cylinder args={[1.5, 1.5, 3, 32]} position={[0, 1.5, 0]}>
                <meshPhysicalMaterial 
                    color="#94a3b8" 
                    transmission={0.95} 
                    opacity={1} 
                    transparent 
                    roughness={0} 
                    ior={1.5} 
                    thickness={0.5}
                    clearcoat={1}
                />
            </Cylinder>
            
            {/* The Fluid Surface (Paraboloid approximation via cylinder top) */}
            <Cylinder args={[1.45, 1.45, 2.0, 32]} position={[0, 1.0, 0]}>
                 <meshStandardMaterial 
                    color="#0891b2" 
                    transparent 
                    opacity={0.4} 
                    emissive="#0891b2" 
                    emissiveIntensity={0.2} 
                 />
            </Cylinder>

            {/* Central Axis/Impeller */}
            <Cylinder args={[0.05, 0.05, 3.5, 16]} position={[0, 1.75, 0]}>
                <meshStandardMaterial color="#64748b" metalness={0.9} roughness={0.1} />
            </Cylinder>

            {/* Base */}
            <Cylinder args={[1.8, 1.8, 0.2, 32]} position={[0, 0, 0]}>
                <meshStandardMaterial color="#1e293b" metalness={0.8} />
            </Cylinder>

            {/* Swirling Particles inside */}
            {[...Array(50)].map((_, i) => {
                const r = 0.5 + Math.random() * 0.8;
                const theta = Math.random() * Math.PI * 2;
                const y = 0.5 + Math.random() * 2;
                // Gold and Cyan tracers
                const col = i % 2 === 0 ? "#fbbf24" : "#22d3ee";
                return <FluidParticle key={i} position={[r * Math.cos(theta), y, r * Math.sin(theta)]} color={col} scale={0.4} />
            })}
        </group>
      </Canvas>
    </div>
  );
}