import React, { useState } from 'react';
import { documentsAPI } from '../api/api';

interface UploadProps {
  onUploadSuccess: () => void;
}

const Upload: React.FC<UploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await documentsAPI.upload(formData);
      
      if (response.data.success) {
        setFile(null);
        onUploadSuccess();
      } else {
        setError(response.data.error || 'Upload failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Upload failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px', marginBottom: '20px' }}>
      <h3>Upload Document</h3>
      <form onSubmit={handleUpload}>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.doc,.docx,.txt"
            style={{ width: '100%' }}
          />
        </div>
        
        {file && (
          <div style={{ marginBottom: '15px', fontSize: '14px', color: '#666' }}>
            Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </div>
        )}

        {error && (
          <div style={{ color: 'red', marginBottom: '15px', padding: '10px', backgroundColor: '#ffebee' }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={!file || isLoading}
          style={{
            padding: '10px 20px',
            backgroundColor: (!file || isLoading) ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            cursor: (!file || isLoading) ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
    </div>
  );
};

export default Upload;
