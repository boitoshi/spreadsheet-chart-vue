<template>
    <div>
      <h2>銘柄別損益推移</h2>
      <!-- 月範囲の選択フォーム -->
      <div class="date-range">
        <label for="start-month">開始月:</label>
        <input type="month" id="start-month" v-model="startMonth" />
        <label for="end-month">終了月:</label>
        <input type="month" id="end-month" v-model="endMonth" />
        <button @click="fetchData">データを取得</button>
      </div>
  
      <!-- グラフの表示 -->
      <LineChart :chart-data="chartData" :chart-options="chartOptions" />
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  import LineChart from './LineChart.vue'; // グラフコンポーネントを使う
  
  const startMonth = ref('2023-01');
  const endMonth = ref('2023-12');
  const chartData = ref(null);
  
  const chartOptions = ref({
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
    },
  });
  
  const fetchData = async () => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/get_data/?start_month=${startMonth.value}&end_month=${endMonth.value}`
      );
      const data = await response.json();
  
      // データを整形してグラフ用にセット
      const labels = data.data.map(row => row[0]); // 日付列
      const datasets = [
        {
          label: '損益推移',
          data: data.data.map(row => parseFloat(row[1])), // 損益列（列番号を調整）
          borderColor: '#36A2EB',
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
        },
      ];
  
      chartData.value = { labels, datasets };
    } catch (error) {
      console.error('データ取得エラー:', error);
    }
  };
  </script>
  
  <style scoped>
  .date-range {
    margin-bottom: 20px;
  }
  </style>
