<template>
  <div id="app">
    <LineChart />
    <StockTable />
    <ProfitChart />
    <Spreadsheet />
  </div>
</template>

<script setup>
import LineChart from "./components/LineChart.vue";
import StockTable from "./components/StockTable.vue";
import ProfitChart from "./components/ProfitChart.vue";
import Spreadsheet from "./components/Spreadsheet.vue";
</script>

<style>
#app {
  max-width: 800px;
  margin: 50px auto;
}
</style>
