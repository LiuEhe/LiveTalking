---
name: 前端代码标准与规范
description: LiveTalking 前端项目的严格代码规范，涵盖 Vue 3、TypeScript、Tailwind CSS 以及组件结构。
---

# LiveTalking 前端代码规范

在为 LiveTalking 前端编写、重构或审查代码时，您**必须**严格遵守以下规则：

## 1. Vue 3 组合式 API (Vue 3 Composition API)
- **`<script setup>`**：所有的 Vue 组件必须使用 TypeScript 环境下的 `<script setup>` 语法 (`<script setup lang="ts">`)。禁止使用选项式 API (Options API)。
- **响应式规范**：首选 `ref` 来定义基础类型，合适的情况下使用 `reactive` 管理对象状态；不过为了保持一致性，通常更推荐通篇使用 `ref`。

## 2. 组件结构 (Component Structure)
- **目录约定**：基础组件应该放置在 `src/components/`，而页面级的视图组件应放置在 `src/views/`。
- **单文件组件 (SFCs)**：模版、脚本和样式需保持在同一个 `.vue` 文件中。**结构顺序必须为：`<template>` -> `<script>` -> `<style>`。**
- **命名规范**：组件文件**必须**使用大驼峰命名法（PascalCase），例如 `UserProfile.vue`。

## 3. Tailwind CSS 样式规范 (Styling with Tailwind CSS)
- **仅限 Tailwind**：在模板中直接使用 Tailwind CSS 工具类来进行样式打磨。尽量避免在 `<style>` 块中编写自定义 CSS，除非是为了处理 Tailwind v4 无法覆盖的复杂动画或极其特殊的设计需求。
- **作用域隔离**：如果迫不得已使用了自定义 CSS，则**必须**加上 `<style scoped>` 属性，以防止样式泄漏污染到其他组件。

## 4. 强类型规范 (TypeScript & Type Safety)
- **全类型覆盖**：对于组件的 prop (`defineProps`)、自定义事件 (`defineEmits`)、状态变量以及 API 返回内容，应当使用明确的 TypeScript 接口或类型进行定义。
- **类型定义存放**：将共享的类型定义抽取统一存放。除非绝对必要，严禁使用 `any` 类型。

## 5. 接口与工具 (API Requests & Utilities)
- **解耦 API 请求**：禁止在 Vue 组件内部直接手写原生的 `fetch` 乃至杂乱的 HTTP 客户端请求。请将所有网络层面的请求抽象为可复用的函数，放置在 `src/utils/` 或者专用的 `api/` 目录下。

## 6. 严格的代码 Review (Mandatory Code Review)
- **质量保证**：在完成任何代码修改或功能添加后，需要进行一次全面的自我审查。
- **正确性**：确保代码运行无暇且没有任何拼写错误，能正确应对各类异常抛出（尤其是与网络请求和 API 交互相关的环节），准确无误实现需求。
