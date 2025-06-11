import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import MonthlyReport from '../views/MonthlyReport.vue'
import ManualInput from '../views/ManualInput.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/report/:month',
    name: 'MonthlyReport',
    component: MonthlyReport
  },
  {
    path: '/input',
    name: 'ManualInput',
    component: ManualInput
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})