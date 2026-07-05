# Physics Presentation (Angular)

Angular port of the Unified Physics research visualization (formerly in `../react`).

## Requirements

- Node.js 20+
- npm 10+

## Development

```bash
cd docs/Presentation_PDF/angular
npm install
npm start
```

Open [http://localhost:4200](http://localhost:4200).

## Build

```bash
npm run build
```

Output: `dist/physics-presentation/`

## Stack

- Angular 19 (standalone components, signals)
- Three.js (hero + fluid scenes)
- KaTeX (math rendering)
- Tailwind CSS (CDN in `index.html`)
- lucide-angular (icons)
- LocalStorage CMS (admin panel, bottom-right gear icon)

## Project layout

```
src/app/
  app.component.*          # Main page shell
  services/cms.service.ts  # Content + admin state
  components/              # Feature components
```

The old `react/` folder can be removed once you have verified this build.
