import axios from 'axios';
import { ref } from 'vue';

export function useSpreadsheetData() {
  const data = ref([]);
  const error = ref(null);
  const loading = ref(false);

  const fetchData = async () => {
    loading.value = true;
    try {
      const response = await axios.get("http://127.0.0.1:8000/get_data/");
      data.value = response.data.data;
    } catch (err) {
      error.value = err;
    } finally {
      loading.value = false;
    }
  };

  return { data, error, loading, fetchData };
}
