import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0e7490",
          dark: "#155e75",
          light: "#ecfeff",
        },
      },
    },
  },
  plugins: [],
};
export default config;
