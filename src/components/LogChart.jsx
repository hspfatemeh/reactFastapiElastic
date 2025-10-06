import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const LogChart = ({ service }) => {
  const [chartData, setChartData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await axios.get('http://127.0.0.1:8000/api/logs', {
          params: { service: service !== 'all' ? service : null }
        });

        const logs = response.data.logs;

        if (Array.isArray(logs) && logs.length > 0) {
          const timestamps = logs.map(log => log.timestamp);
          const totalRequests = logs.map(log => log.total_requests);
          const successfulRequests = logs.map(log => log.successful_requests);
          const errorRequests = logs.map(log => log.error_requests);
          const successfulResponseTime = logs.map(log => log.successful_response_time); 

          setChartData({
            labels: timestamps,
            datasets: [
              {
                label: 'Total Requests',
                data: totalRequests,
                borderColor: 'rgba(75,192,192,1)',
                backgroundColor: 'rgba(75,192,192,0.4)',
                fill: false,
                yAxisID: 'y-axis-requests',
              },
              // {
              //   label: 'Successful Requests',
              //   data: successfulRequests,
              //   borderColor: 'rgba(75,192,75,1)',
              //   backgroundColor: 'rgba(255,159,64,0.4)',
              //   fill: false,
              //   yAxisID: 'y-axis-requests',
              // },
              {
                label: 'Error Requests',
                data: errorRequests,
                borderColor: 'rgba(192,75,75,1)',
                backgroundColor: 'rgba(192,75,75,0.4)',
                fill: false,
                yAxisID: 'y-axis-requests',
              },
              {
                label: 'Successful Response Time',
                data: successfulResponseTime, 
                borderColor: 'rgba(75,192,75,1)',
                backgroundColor: 'rgba(75,192,75,0.4)',
                fill: false,
                yAxisID: 'y-axis-response', 
              }
            ],
          });
        } else {
          setError('No log data available');
        }
      } catch (err) {
        setError('Error fetching log data');
        console.error('Error fetching logs:', err);
      } finally {
        setLoading(false);
      }
    };

    const timeout = setTimeout(() => {
      fetchData();
    }, 5000);

    return () => clearTimeout(timeout);
  }, [service]);

  return (
    <div className="max-w-8xl mx-auto p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4 text-center">Logs for {service === 'all' ? 'All Services' : service}</h2>
      {loading ? (
        <p className="text-blue-500">Loading...</p>
      ) : error ? (
        <p className="text-red-500">{error}</p>
      ) : (
        chartData && (
          <div className="relative h-96">
            <Line
              data={chartData}
              options={{
                maintainAspectRatio: false,
                scales: {
                  'y-axis-response': {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    grid: {
                      drawOnChartArea: false,
                    },
                    title: {
                      display: true,
                      text: 'Response Time (ms)',
                    },
                  },
                  'y-axis-requests': {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: true,
                    grid: {
                      drawOnChartArea: true,
                    },
                    title: {
                      display: true,
                      text: 'Request Count',
                    },
                  },
                },
              }}
            />
          </div>
        )
      )}
    </div>
  );
};

export default LogChart;
