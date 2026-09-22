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
          DEFAULT: '#0F3D3B',
          deep: '#0A2B29',
        },
        forest: {
          DEFAULT: '#1F6F54',
          soft: '#E7EFE9',
        },
        paper: {
          DEFAULT: '#F5F3EC',
          raised: '#FFFFFF',
        },
        ink: {
          DEFAULT: '#26241F',
          soft: '#5B5A54',
          faint: '#8B887C',
        },
        line: '#DFDACB',
        ochre: {
          DEFAULT: '#B9852F',
          deep: '#8F6620',
          soft: '#F5E9D4',
        },
        done: '#3E7C5A',
        warn: {
          DEFAULT: '#B5502E',
          soft: '#F6E4DA',
        },
      },
    },
  },
  plugins: [],
}
