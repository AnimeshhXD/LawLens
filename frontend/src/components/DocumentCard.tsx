import React from 'react';
import { Document } from '../api/api';

interface DocumentCardProps {
  document: Document;
  onSelect: (document: Document) => void;
  isSelected: boolean;
}

const DocumentCard: React.FC<DocumentCardProps> = ({ document, onSelect, isSelected }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div
      onClick={() => onSelect(document)}
      style={{
        border: isSelected ? '2px solid #007bff' : '1px solid #ddd',
        borderRadius: '8px',
        padding: '15px',
        marginBottom: '10px',
        cursor: 'pointer',
        backgroundColor: isSelected ? '#f8f9fa' : 'white',
        transition: 'all 0.2s ease'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = '#f0f0f0';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = isSelected ? '#f8f9fa' : 'white';
      }}
    >
      <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>{document.filename}</h4>
      <p style={{ margin: '0', color: '#666', fontSize: '14px' }}>
        Uploaded: {formatDate(document.upload_date)}
      </p>
    </div>
  );
};

export default DocumentCard;
