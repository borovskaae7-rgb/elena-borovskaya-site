import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['var(--font-sans)', 'Inter', 'system-ui', 'sans-serif'] },
      colors: { ink: '#17211f', sage: '#48665d', clay: '#c77e5a', cream: '#f7f4ee' },
      boxShadow: { soft: '0 24px 80px rgba(23, 33, 31, 0.10)' }
    }
  },
  plugins: []
};
export default config;
