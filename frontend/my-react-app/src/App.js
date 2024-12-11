import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './App.css';

function App() {
    const [file, setFile] = useState(null);
    const navigate = useNavigate();

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const redirectToRegClass = () => {
        navigate('/choose-regclass');
    };

    const redirectToTemplate = () => {
        navigate('/choose-template', { state: { file } }); 
    };
    const redirectToDownloadPage = () => {
        navigate('/download-page');
    };

    return (
        <div className="App">
            <div className="wrapper">
                <h1>Upload Excel File</h1>
                <form>
                <div className="file-input-group">
                    <input type="file" onChange={handleFileChange} />
                    <button type="button" className="download-button" onClick={redirectToDownloadPage}>
                            Download an Existing Table
                        </button>
                        </div>
                    {file && (
                        <div className="button-group">
                            <button className="btn-left" type="button" onClick={redirectToRegClass}>
                                Choose Existing Reg Class
                            </button>
                            <button className="btn-right" type="button" onClick={redirectToTemplate}>
                                Choose Template
                            </button>
                        </div>
                    )}
                </form>
            </div>
        </div>
    );
}

export default App;
