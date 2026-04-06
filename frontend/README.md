# LiveTalking 前端项目 (Vue 3 + Vite)

本文档说明了本项目前端部分的配置、安装与运行指南。本项目由原先的混合架构分离为了前后端分离架构。

## 技术栈概述
* **框架**: Vue 3 (Composition API)
* **工程化构建**: Vite
* **语言**: TypeScript
* **样式框架**: Tailwind CSS v4
* **路由管控**: Vue Router 4

---

## 快速上手

### 1. 环境准备
确保您的本地已经安装了较高版本的 Node.js（推荐 `Node.js 18+`）。通过 `node -v` 检查版本。

### 2. 安装项目依赖
进入前端目录，并使用 npm 安装所有的依赖资源：
```bash
cd frontend
npm install
```

### 3. 本地开发服务器
运行 Vite 提供的本地开发命令：
```bash
npm run dev
```
此时 Vite 会自动启动开发服务器（由于 Vite 配置了 `open: true`，此时会在浏览器中自动打开该项目地址，例如 `http://127.0.0.1:5173/`）。页面的更改可以秒级热更新 (HMR)。

---

## 核心架构说明

为了保证前端的规范性和代码可维护性，我们在 `src` 目录下规定了以下子目录的用法：

* **`router/`**: \`index.ts\` 负责整个应用的路由管理，所有的路由映射都应该在此修改。
* **`views/`**: 用于存放页面级别的视图 Vue 组件（例如 \`HomeView.vue\`），由 router 进行访问展示。
* **`utils/`**: 存放所有与业务无关的、通用的 TypeScript 辅助函数库。比如日期格式化函数、统一的 Axios HTTP 接口请求封装等。
* **`types/`**: 当我们需要处理后端返回的 JSON 数据时，统一将 TypeScript 接口定义 (`interfaces` 和 `types`) 存放在此文件夹内，保持强类型约束的规范。
* **`style.css`**: Tailwind CSS v4 的主入口，全局变量及基础配置在此通过 `@import "tailwindcss";` 和 原生 CSS 变量实现。

---

## 后续开发预备

接下来可以通过在 `utils` 目录下封装统一的 API 请求库，对接现有的 FastAPI 后端接口实现前后端的正式联调。
