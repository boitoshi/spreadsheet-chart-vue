<template>
  <div>
    <h2>株価推移</h2>
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale } from 'chart.js'
import { Line } from 'vue-chartjs'

// Chart.jsのプラグイン登録
ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale)

const chartData = ref({
  labels: ['1月', '2月', '3月'], // 月別ラベル
  datasets: [
    {
      label: 'DeNA',
      backgroundColor: '#FF6384',
      borderColor: '#FF6384',
      data: [2100, 2150, 2120], // ダミーデータ
    },
    {
      label: '任天堂',
      backgroundColor: '#36A2EB',
      borderColor: '#36A2EB',
      data: [5600, 5700, 5650], // ダミーデータ
    },
  ],
})

const chartOptions = ref({
  responsive: true,
  // 他のオプションをここに追加
})
</script>

<style scoped>
h2 {
  text-align: center;
  margin-bottom: 20px;
}
</style>
