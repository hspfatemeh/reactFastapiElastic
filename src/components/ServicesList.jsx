import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LogChart from './LogChart';

const ServicesList = () => {
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/services');
        const servicesWithCounts = response.data.services.map(service => ({
          name: service.key,
          count: service.doc_count
        }));
        setServices([{ name: 'all', count: servicesWithCounts.reduce((total, service) => total + service.count, 0) }, ...servicesWithCounts]);
      } catch (err) {
        setError('Error fetching services');
        console.error('Error fetching services:', err);
      }};

    fetchServices();
  }, []);
  const handleServiceSelect = (service) => {
    setSelectedService(service);
  };


  return (
    <div className="max-w-4xl mx-auto p-8 bg-white shadow-md rounded-lg">
      <h1 className="text-3xl font-bold mb-4 text-center">Available Services</h1>
      {error ? <p className="text-red-500">{error}</p> : (
        <ul className="list-disc list-inside mb-4">
          {services.map(service => (
            <li 
              key={service.name} 
              className="cursor-pointer hover:text-blue-500" 
              onClick={() => handleServiceSelect(service.name)}
            >
              {service.name} ({service.count})
            </li>
          ))}
        </ul>)}
   
      {selectedService && (
        <div className="mt-8">
          <LogChart service={selectedService} />
        </div>
      )}
    </div>);};

export default ServicesList;
