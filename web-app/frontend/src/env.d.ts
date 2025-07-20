/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_DESCRIPTION: string
  readonly NODE_ENV: 'development' | 'production' | 'test'
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Chart.js module declaration for better type support
declare module 'chart.js' {
  interface ChartTypeRegistry {
    // Custom chart types can be declared here if needed
  }
}

// Additional Vue Router type support
declare module 'vue-router' {
  interface RouteMeta {
    // Custom route meta properties can be declared here
    title?: string
    requiresAuth?: boolean
  }
}