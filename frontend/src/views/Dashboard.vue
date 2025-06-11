<template>
  <div class="dashboard">
    <h1>株式ポートフォリオ ダッシュボード</h1>
    
    <div class="dashboard-grid">
      <div class="dashboard-card">
        <PortfolioDashboard />
      </div>
      
      <div class="dashboard-card">
        <Spreadsheet />
      </div>
      
      <div class="dashboard-card">
        <ProfitChart />
      </div>
      
      <div class="dashboard-card">
        <LineChart />
      </div>
    </div>
    
    <div class="navigation-links">
      <router-link to="/input" class="nav-button">
        手動データ入力
      </router-link>
      <router-link to="/report/2024-01" class="nav-button">
        月次レポート
      </router-link>
    </div>
  </div>
</template>

<script>
import PortfolioDashboard from '../components/portfolio/PortfolioDashboard.vue'
import Spreadsheet from '../components/portfolio/Spreadsheet.vue'
import ProfitChart from '../components/charts/ProfitChart.vue'
import LineChart from '../components/charts/LineChart.vue'

export default {
  name: 'Dashboard',
  components: {
    PortfolioDashboard,
    Spreadsheet,
    ProfitChart,
    LineChart
  }
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.dashboard-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  padding: 20px;
}

.navigation-links {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}

.nav-button {
  display: inline-block;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 25px;
  transition: transform 0.3s ease;
  font-weight: 600;
}

.nav-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .navigation-links {
    flex-direction: column;
    align-items: center;
  }
}
</style>