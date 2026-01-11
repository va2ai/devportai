# RAG Fact-Check Frontend

React + Vite + Tailwind CSS frontend for the RAG Fact-Check application.

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── main.jsx        # Application entry point
├── App.jsx         # Main application component
├── App.css         # Application styles
└── index.css       # Global styles with Tailwind
```

## Features

- ✨ React 18 with JSX support
- 🎨 Tailwind CSS for styling
- ⚡ Vite for fast development and builds
- 🔄 Hot module replacement (HMR)
- 📦 Optimized production builds
- 🛠️ ESLint for code quality

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Styling

This project uses Tailwind CSS for styling. All Tailwind utilities are available in JSX components.

### Customization

Edit `tailwind.config.js` to customize:
- Color schemes
- Typography
- Spacing
- Breakpoints
- And more

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Technologies

- **React** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **PostCSS** - CSS transformation
- **Autoprefixer** - CSS vendor prefixing

## Performance

- Code splitting with dynamic imports
- CSS minification and purging with Tailwind
- Image optimization support
- Lazy loading components

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Future Enhancements

- [ ] State management (Redux/Zustand)
- [ ] React Router for multi-page navigation
- [ ] Unit and integration tests
- [ ] Component library
- [ ] PWA support
