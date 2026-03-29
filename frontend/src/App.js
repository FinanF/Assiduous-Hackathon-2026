import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Slider } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { exportPNG, exportExcel, exportPDF } from './exportUtils';
import axios from 'axios';

function App() {
  const [data, setData] = useState(null);
  const [health, setHealth] = useState(null);
  const [nthQuater, setNthQuater] = useState(4);
  const chartRef = useRef();


  const fetchSyncData = useCallback(async () => {
    try {
      const response = await axios.post('http://localhost:8000/sync-data');
      setHealth(response.status);
      console.log('Synced!');
    } catch (error) {
      setHealth(error.response?.status || 0);
      console.error('Sync failed:', error.response?.status);
    }
  }, []);

  const fetchForecast = useCallback(async () => {
    try {
      const response = await axios.get(`http://localhost:8000/forecast/${nthQuater}`);
      setData(response.data);
    } catch (error) {
      console.error('Forecast error:', error);
    }
  }, [nthQuater]);

  const handlePNG = () => exportPNG(chartRef, `forecast-${nthQuater}q.png`);
  const handleExcel = () => exportExcel(chartData, `forecast-${nthQuater}q.xlsx`);
  const handlePDF = () => exportPDF(chartRef, `forecast-${nthQuater}q.pdf`);


  useEffect(() => {
    fetchSyncData();
  }, [fetchSyncData]);

  useEffect(() => {
    if (health === 200) {
      fetchForecast();
    }
  }, [health, fetchForecast]);

  if (!data) {
    return (
      <div style={{padding: '20px', textAlign: 'center'}}>
        <div>Loading forecast data...</div>
        <div>Health: {health === 200 ? 'Ready' : health || 'Connecting'}</div>
      </div>
    );
  }

  const chartData = data.predictions.base.map((base, i) => ({
    quarter: `Q${i+1}`,
    base,
    upside: data.predictions.upside[i],
    downside: data.predictions.downside[i]
  }));

  return (
    <div style={{padding: '20px', maxWidth: '1000px', margin: '0 auto'}}>
      <h1>IBM EPS Forecast</h1>
      <div style={{marginBottom: '20px'}}>
        <button onClick={fetchSyncData} style={{marginRight: '10px'}}>
          Sync Data
        </button>
        <button onClick={fetchForecast}>Refresh Forecast</button>
        <div>Status: {health === 200 ? 'Ready' : 'Connecting...'}</div>
      </div>

      <div style={{marginBottom: '20px'}}>
        <label>Quarters: {nthQuater}</label>
        <Slider
          size="small"
          value={nthQuater}
          min={4}
          max={20}
          aria-label="Quarters"
          valueLabelDisplay="auto"
          onChange={(event, value) => setNthQuater(value)}
        />
      </div>
        <div ref={chartRef}>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="quarter" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="base" stroke="#8884d8" name="Base Case" />
              <Line type="monotone" dataKey="upside" stroke="#82ca9d" name="Upside" />
              <Line type="monotone" dataKey="downside" stroke="#ff7300" name="Downside" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div style={{marginBottom: '20px'}}>
        <button onClick={handlePNG}>PNG</button>
        <button onClick={handleExcel}>Excel</button>
        <button onClick={handlePDF}>PDF</button>
      </div>

    </div>
  );
}

export default App;