<template>
  <div>
    <h2>株価推移</h2>
    <div class="select-box">
      <label for="stock-select">銘柄を選択：</label>
      <select id="stock-select" v-model="selectedStock" @change="updateChartData">
        <option value="all">すべて</option>
        <option v-for="stock in stockOptions" :key="stock" :value="stock">
          {{ stock }}
        </option>
      </select>
    </div>
    <Line :key="selectedStock" :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale } from 'chart.js'
import { Line } from 'vue-chartjs'

// Chart.jsのプラグイン登録
ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale)

//銘柄データ（仮）
const allStockData = ref([
  { name: 'DeNA', data: [2100, 2150, 2120] },
  { name: '任天堂', data: [5600, 5700, 5650] },
]);

const stockOptions = ref(allStockData.value.map((stock) => stock.name));
const selectedStock = ref('all');

const chartData = ref({
  labels: ['1月', '2月', '3月'], // 月別ラベル
  datasets: allStockData.value.map(stock => ({
    label: stock.name,
    backgroundColor: stock.name === "DeNA" ? '#FF6384' : '#36A2EB',
    borderColor: stock.name === "DeNA" ? '#FF6384' : '#36A2EB',
    data: stock.data,
  })),
});

const chartOptions = ref({
  responsive: true,
  // 他のオプションをここに追加
});

// グラフデータ更新関数
const updateChartData = () => {
  const allColors = {
    "DeNA": { background: '#FF6384', border: '#FF6384' },
    "任天堂": { background: '#36A2EB', border: '#36A2EB' }
  };

  let updatedDatasets;

  if (selectedStock.value === 'all') {
    updatedDatasets = allStockData.value.map(stock => ({
      label: stock.name,
      backgroundColor: allColors[stock.name]?.background || '#CCCCCC',
      borderColor: allColors[stock.name]?.border || '#CCCCCC',
      data: stock.data,
    }));
  } else {
    const stock = allStockData.value.find(stock => stock.name === selectedStock.value);
    if (stock) {
      updatedDatasets = [{
        label: stock.name,
        backgroundColor: allColors[stock.name]?.background || '#CCCCCC',
        borderColor: allColors[stock.name]?.border || '#CCCCCC',
        data: stock.data,
      }];
    } else {
      console.warn("選択した銘柄がデータに見つかりません: ", selectedStock.value);
      updatedDatasets = []; // データがない場合は空にする
    }
  }

  // 新しいオブジェクトとして設定
  chartData.value = {
    labels: chartData.value.labels, // ラベルはそのまま再利用
    datasets: updatedDatasets,
  };
};

</script>

<style scoped>
h2 {
  text-align: center;
  margin-bottom: 20px;
}

.select-box {
  margin-bottom: 20px;
  text-align: center;
}

select {
  padding: 5px;
  font-size: 14px;
}
</style>
