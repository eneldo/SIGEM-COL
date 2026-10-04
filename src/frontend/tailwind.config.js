/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pine: {
          DEFAULT: 'rgb(var(--pine) / <alpha-value>)',
          deep: 'rgb(var(--pine-deep) / <alpha-value>)',
        },
        forest: {
          DEFAULT: 'rgb(var(--forest) / <alpha-value>)',
          soft: 'rgb(var(--forest-soft) / <alpha-value>)',
        },
        paper: {
          DEFAULT: 'rgb(var(--paper) / <alpha-value>)',
          raised: 'rgb(var(--paper-raised) / <alpha-value>)',
        },
        ink: {
          DEFAULT: 'rgb(var(--ink) / <alpha-value>)',
          soft: 'rgb(var(--ink-soft) / <alpha-value>)',
          faint: 'rgb(var(--ink-faint) / <alpha-value>)',
        },
        line: 'rgb(var(--line) / <alpha-value>)',
        ochre: {
          DEFAULT: 'rgb(var(--ochre) / <alpha-value>)',
          deep: 'rgb(var(--ochre-deep) / <alpha-value>)',
          soft: 'rgb(var(--ochre-soft) / <alpha-value>)',
        },
        done: 'rgb(var(--done) / <alpha-value>)',
        warn: {
          DEFAULT: 'rgb(var(--warn) / <alpha-value>)',
          soft: 'rgb(var(--warn-soft) / <alpha-value>)',
        },
      },
    },
  },
  plugins: [],
}
