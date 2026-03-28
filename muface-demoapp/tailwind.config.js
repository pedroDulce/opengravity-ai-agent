/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        primary: "#0056D2",
        "on-primary": "#FFFFFF",
        "primary-container": "#D7E2FF",
        "on-primary-container": "#001945",
        surface: "#F8F9FF",
        "on-surface": "#191C20",
        "surface-container-lowest": "#FFFFFF",
        "surface-container-low": "#F3F3FA",
        "surface-container": "#EEEEF6",
        "surface-container-high": "#E8E7F0",
        "surface-container-highest": "#E2E2E9",
        "on-surface-variant": "#43474E",
        outline: "#73777F",
        "outline-variant": "#C3C6CF",
        "tertiary-fixed": "#FFDBCF",
        "on-tertiary-fixed-variant": "#8B1A00",
      },
    },
  },
  plugins: [],
}