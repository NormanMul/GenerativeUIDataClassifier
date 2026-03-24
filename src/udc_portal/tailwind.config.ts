import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "udc-blue": "#1e40af",
        "udc-green": "#16a34a",
        "udc-purple": "#7c3aed",
        "udc-orange": "#ea580c",
        "udc-gray": "#4b5563",
      },
    },
  },
  plugins: [],
};

export default config;
