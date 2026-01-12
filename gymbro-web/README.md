# Gym Bro Web Frontend

React + Vite + TypeScript + TailwindCSS PWA.

## Quick Start

```bash
cd gymbro-web
npm install
npm run dev
```

Visit `http://localhost:5173`. The dev server proxies `/api/*` to `http://localhost:8000`.

## Build

```bash
npm run build
npm run preview
```

## Structure

- `src/main.tsx` — Entry point
- `src/App.tsx` — Main app component
- `src/index.css` — Global styles (Tailwind)
- `public/manifest.json` — PWA manifest
- `public/sw.js` — Service Worker (basic offline support)
