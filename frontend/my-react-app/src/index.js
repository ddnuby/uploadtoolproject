import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'; // Import Router and Routes
import './index.css';
import App from './App';
import DownloadPage from './DownloadPage';
import ChooseRegClass from './ChooseRegClass'; // Make sure to import your components
import ChooseTemplate from './ChooseTemplate'; // Import the necessary components
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/download-page" element={<DownloadPage/>}/>
        <Route path="/choose-regclass" element={<ChooseRegClass />} />
        <Route path="/choose-template" element={<ChooseTemplate />} />
      </Routes>
    </Router>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
