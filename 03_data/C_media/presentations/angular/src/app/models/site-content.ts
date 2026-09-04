export interface Paper {
  id: string;
  title: string;
  color: string;
  tag: string;
}

export interface SiteContent {
  hero: {
    badge: string;
    title: string;
    subtitle: string;
    description: string;
  };
  intro: {
    title: string;
    body: string[];
  };
  author: {
    name: string;
    role: string;
    location: string;
    email: string;
  };
  papers: Paper[];
}

export const DEFAULT_CONTENT: SiteContent = {
  hero: {
    badge: 'Physics Research • Nov 2025',
    title: 'Unified Physics',
    subtitle: 'Fluid Analogues',
    description:
      'Exploring deep algebraic connections between classical hydrodynamics, relativistic time dilation, and the fundamental scales of the electron.',
  },
  intro: {
    title: 'Bridging Scales',
    body: [
      'The electron occupies a central role in both classical and quantum theories of matter. Its properties are defined by three distinct scales: the classical radius, the Compton wavelength, and the Bohr radius.',
      'This research series presents a unified view where these scales combine in a simple harmonic oscillator construction. Furthermore, it explores how classical fluid mechanics—specifically vortex dynamics and swirling flows—can provide robust analogues for relativistic phenomena like time dilation and gravitational acceleration.',
    ],
  },
  author: {
    name: 'Omar Iskandarani',
    role: 'Independent Researcher',
    location: 'Groningen, The Netherlands',
    email: 'info@omariskandarani.com',
  },
  papers: [
    {
      id: '1',
      title:
        'A Unified Electron Scale Relation from Classical Radius, Compton Frequency, and Hydrogen Energy',
      color: 'text-physics-purple',
      tag: 'Paper I',
    },
    {
      id: '2',
      title:
        'Rotational Kinetic Energy Density and an Effective Mass Relation in Incompressible Fluids',
      color: 'text-physics-cyan',
      tag: 'Paper II',
    },
    {
      id: '3',
      title:
        'Circulation, Rigid Rotation, and Proper Time Dilation: A Fluid Representation',
      color: 'text-physics-gold',
      tag: 'Paper III',
    },
    {
      id: '4',
      title:
        'Energy, Impulse, and Stability of Thin Vortex Loops in Incompressible Fluids',
      color: 'text-physics-cyan',
      tag: 'Paper IV',
    },
    {
      id: '5',
      title:
        'Swirl Pressure and Effective Gravitational Acceleration in Rotating Flows',
      color: 'text-physics-gold',
      tag: 'Paper V',
    },
    {
      id: '6',
      title:
        'Impulsive Axisymmetric Forcing in a Rotating Cylinder and Skyrmionic Photon Fields',
      color: 'text-physics-purple',
      tag: 'Paper VI',
    },
  ],
};
