import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#1a7f5a",  // Tunisian green
        accent: "#e8a020",   // warm gold
      },
    },
  },
  plugins: [],
} satisfies Config;
