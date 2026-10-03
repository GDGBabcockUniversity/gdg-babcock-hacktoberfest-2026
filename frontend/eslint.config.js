import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  // 1. Include recommended rules for JavaScript
  js.configs.recommended,
  
  // 2. Include recommended rules for TypeScript
  ...tseslint.configs.recommended,
  
  // 3. Custom configuration overrides
  {
    files: ["**/*.{js,mjs,cjs,ts,tsx}"],
    rules: {
      // Add any specific rules you want to turn on/off here
      "no-unused-vars": "warn"
    }
  },
  
  // 4. Global ignore patterns (Replaces .eslintignore)
  {
    ignores: ["node_modules/", "dist/", "build/"]
  }
);
