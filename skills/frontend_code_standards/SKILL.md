---
name: Frontend Code Standards and Guidelines
description: Strict coding guidelines for the LiveTalking frontend project, covering Vue 3, TypeScript, Tailwind CSS, and component structure.
---

# LiveTalking Frontend Code Standards

When writing, refactoring, or reviewing code for the LiveTalking frontend, you MUST strictly adhere to the following rules:

## 1. Vue 3 Composition API (Vue 3 组合式 API)
- **`<script setup>`**: ALL Vue components must use the `<script setup>` syntax with TypeScript (`<script setup lang="ts">`). Do not use the Options API.
- **Reactivity**: Prefer `ref` for primitive types and `reactive` for object-state where appropriate, though `ref` is generally preferred for consistency.

## 2. Component Structure (组件结构)
- **Directory**: Components should be placed in `src/components/`, while page-level views belong in `src/views/`.
- **Single File Components (SFCs)**: Keep template, script, and style in the same `.vue` file.
- **Naming**: Component files MUST be named in PascalCase (e.g., `UserProfile.vue`).

## 3. Styling with Tailwind CSS (样式规范)
- **Tailwind Only**: Use Tailwind CSS utility classes directly in the template for styling. Avoid writing custom CSS in `<style>` blocks unless absolutely necessary for complex animations or specific design requirements not covered by Tailwind v4.
- **Scoped Styles**: If custom CSS is unavoidable, it MUST use `<style scoped>` to prevent styles from leaking to other components.

## 4. TypeScript & Type Safety (强类型规范)
- **Explicit Types**: Use explicit TypeScript interfaces or types for component props (`defineProps`), emits (`defineEmits`), state variables, and API responses.
- **Type Definitions**: Place shared type definitions in the `src/type/` directory. Do not use `any` types unless absolutely necessary.

## 5. API Requests & Utilities (接口与工具)
- **API Separation**: Do not write raw `fetch` or HTTP client calls directly inside Vue components. Extract them into reusable functions placed in `src/utils/` or a dedicated `api/` directory.

## 6. Mandatory Code Review (严格代码 Review)
- **Quality Assurance**: After completing any code modifications or feature additions, perform a self-review of the changes.
- **Correctness**: Ensure that the code functions flawlessly without typos, properly handles errors (especially in API interactions), and correctly implements the required features.
