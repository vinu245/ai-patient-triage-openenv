/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0a1020",
        panel: "rgba(20, 28, 48, 0.65)",
        glow: "#29d3a1",
        sky: "#4cc9f0",
        coral: "#ff7f6b",
        amber: "#ffb703",
      },
      boxShadow: {
        glass: "0 12px 40px rgba(0, 0, 0, 0.35)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      fontFamily: {
        display: ["Sora", "sans-serif"],
        body: ["Manrope", "sans-serif"],
      },
      animation: {
        floatIn: "floatIn 420ms ease-out forwards",
        pulseSoft: "pulseSoft 2.4s infinite",
      },
      keyframes: {
        floatIn: {
          "0%": { opacity: "0", transform: "translateY(10px) scale(0.99)" },
          "100%": { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.72" },
        },
      },
    },
  },
  plugins: [],
};
