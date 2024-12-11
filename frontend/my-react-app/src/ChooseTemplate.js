import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import * as XLSX from 'xlsx';
import './ChooseTemplate.css';
import { ToastContainer, toast} from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function ChooseTemplate() {
    const location = useLocation();
    const { file: initialFile } = location.state || {}; 
    const [file, setFile] = useState(initialFile); 
    const [selectedDatabase, setSelectedDatabase] = useState(''); 
    const [message, setMessage] = useState('');
    const [databases, setDatabases] = useState([]); 
    const [tableNames, setTableNames] = useState([]); 
    const [worksheetNames, setWorksheetNames] = useState([]); 
    const [matchingTableNames, setMatchingTableNames] = useState([]); 
    const [uploadComplete, setUploadComplete] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchDatabases = async () => {
            try {
                const response = await axios.get('/backend/get-databases');
                console.log(response.data); 
                setDatabases(response.data);
            } catch (error) {
                console.error('Error fetching databases:', error);
            }
        };

        fetchDatabases();
    }, []); 

    const handleDatabaseChange = async (e) => {
        const selectedDb = e.target.value; 
        setSelectedDatabase(selectedDb);
        try {
            const response = await axios.get('/backend/get-table-names?database_name=${selectedDb}');
            const fetchedTableNames = response.data.table_names || [];
            setTableNames(fetchedTableNames);

            
            const matches = fetchedTableNames.filter(tableName => 
                worksheetNames.includes(tableName)
            );
            setMatchingTableNames(matches);
        } catch (error) {
            console.error('Error fetching table names: ', error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', file); 
        formData.append('database', selectedDatabase); 

        try {
            const response = await axios.post('/backend/upload-excel', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            toast.success("Successful Upload! Redirecting...", {
                autoClose: 2000,
                onClose:() => navigate(-1),
            });
           setMessage(response.data.message);
            setUploadComplete(true);
        } catch (error) {
            setUploadComplete(false);
            if (error.response) {
                if (error.response.status === 409) {
                    setMessage(`Error: Table already exists ${error.response.data.message}`);
                }
                else if (error.response.status === 404) {
                    setMessage(`Error: Table does not exist yet ${error.response.data.message}`);
                }
                else if (error.response.status == 400){
                    setMessage(`Error: ${error.response.data.message}`)
                }
            }else{
                setMessage('An unexpected error has occured. Please, try again or contact someone');               
            }
        }
    };

    return (
        <div className="template-container">
            <h2>Choose a Template and Database</h2>

            <label htmlFor="database">Choose Database:</label>
            <select id="database" value={selectedDatabase} onChange={handleDatabaseChange}>
                <option value="" disabled>Select a database</option>
                {databases.map((db, index) => (
                    <option key={index} value={db}>
                        {db}
                    </option>
                ))}
            </select>

            <br />
            {selectedDatabase && file && (
                <div>
                    <h3>Upload Excel File</h3>
                    <button type="submit" onClick={handleSubmit}>
                        Upload
                    </button>
                </div>
            )}

            {message && <p>{message}</p>}
            <ToastContainer/>
        </div>
    );
}

export default ChooseTemplate;


