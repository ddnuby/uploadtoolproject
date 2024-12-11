import React, { useState, useEffect } from 'react';
import axios from 'axios'; 
import './DownloadPage.css';

function DownloadPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [database, setDatabase] = useState([]);
  const [filteredResults, setFilteredResults] = useState([]);

  console.log("This is the database");
  console.log(database);
  console.log("This is the filtered result:");
  console.log(filteredResults);

  useEffect(() => {
    const fetchDatabase = async () => {
      try {
        const response = await axios.get('/backend/search-database', {
          params: { query: '' },
          headers: { 'Cache-Control': 'no-cache' },
        });
        setDatabase(response.data);
        setFilteredResults(response.data);
      } catch (error) {
        console.error('Error fetching the databases', error);
      }
    };
    fetchDatabase();
  }, []);
  const handleDownload = async (databaseName) => {
    try {
      const response = await axios.get('/backend/download-table', {
        params: { database_name: databaseName},
        responseType: 'blob', 
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${databaseName}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading the table:', error);
    }
  };
  const handleSearchInputChange = (event) => {
    setSearchQuery(event.target.value);
  };
  const handleSearch = async () => {
    try {
      const response = await axios.get('/backend/search-database', {
        params: { query: searchQuery },
        headers: { 'Cache-Control': 'no-cache' },
      });
      setFilteredResults(response.data);
    } catch (error) {
      console.error('Error searching the databases', error);
    }
  };

  return (
    <div className="container">
      <input
        type="text"
        placeholder="Search templates"
        value={searchQuery}
        onChange={handleSearchInputChange}
      />
      <button onClick={handleSearch}>Search</button>
      <ul>
        {filteredResults.map((db, index) => (
          <li key={index}>
          {db}
          <button onClick={() => handleDownload(db)}>Download</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default DownloadPage;
