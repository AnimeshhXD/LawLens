import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { documentsAPI, Document } from '../api/api';
import DocumentCard from '../components/DocumentCard';
import Upload from '../components/Upload';
import AnalysisResult from '../components/AnalysisResult';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setIsLoading(true);
      const response = await documentsAPI.getDocuments();
      if (response.success) {
        setDocuments(response.data);
      } else {
        setError(response.error || 'Failed to fetch documents');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch documents');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadSuccess = () => {
    fetchDocuments();
  };

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document);
    setAnalysisResult(null);
  };

  const handleAnalysisComplete = (result: any) => {
    setAnalysisResult(result);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h1>LawLens Dashboard</h1>
        <div>
          <span style={{ marginRight: '20px' }}>Welcome, {user?.email}</span>
          <button
            onClick={logout}
            style={{
              padding: '8px 16px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
        <div>
          <h2>Documents</h2>
          <Upload onUploadSuccess={handleUploadSuccess} />
          
          {error && (
            <div style={{ color: 'red', margin: '15px 0', padding: '10px', backgroundColor: '#ffebee' }}>
              {error}
            </div>
          )}

          {isLoading ? (
            <div>Loading documents...</div>
          ) : (
            <div style={{ marginTop: '20px' }}>
              {documents.length === 0 ? (
                <p>No documents uploaded yet.</p>
              ) : (
                documents.map((doc) => (
                  <DocumentCard
                    key={doc.id}
                    document={doc}
                    onSelect={handleDocumentSelect}
                    isSelected={selectedDocument?.id === doc.id}
                  />
                ))
              )}
            </div>
          )}
        </div>

        <div>
          <h2>Analysis</h2>
          {selectedDocument ? (
            <AnalysisResult
              document={selectedDocument}
              onAnalysisComplete={handleAnalysisComplete}
            />
          ) : (
            <p>Select a document to analyze</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
