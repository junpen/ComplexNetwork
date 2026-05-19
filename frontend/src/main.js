/**
 * 应用入口文件
 * 负责创建 Vue 应用实例、挂载根组件到 DOM
 */

// 从 Vue 中导入 createApp 工厂函数，用于创建应用实例
import { createApp } from 'vue'
// 导入根组件 App.vue
import App from './App.vue'

// 创建 Vue 应用实例并传入根组件
const app = createApp(App)
// 将应用挂载到 HTML 中 id 为 "app" 的 DOM 元素上
app.mount('#app')
