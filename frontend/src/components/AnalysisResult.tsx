import React, { useState } from 'react';
import { Document, analysisAPI, RegulatoryChangeCreate, RegulatoryImpactAnalysisRequest } from '../api/api';

interface AnalysisResultProps {
  document: Document;
  onAnalysisComplete: (result: any) => void;
}

const AnalysisResult: React.FC<AnalysisResultProps> = ({ document, onAnalysisComplete }) => {
  const [activeAnalysis, setActiveAnalysis] = useState<'risk' | 'regulatory' | 'reputation' | 'impact' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const [regulatoryData, setRegulatoryData] = useState<RegulatoryChangeCreate>({
    change_type: '',
    description: '',
    effective_date: ''
  });

  const [impactData, setImpactData] = useState<RegulatoryImpactAnalysisRequest>({
    scenario: '',
    timeframe: ''
  });

  const handleRiskAnalysis = async () => {
    setActiveAnalysis('risk');
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await analysisAPI.assessRisk(document.id);
      if (response.success) {
        setResult(response.data);
        onAnalysisComplete(response.data);
      } else {
        setError(response.error || 'Risk analysis failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Risk analysis failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegulatoryAnalysis = async () => {
    if (!regulatoryData.change_type || !regulatoryData.description || !regulatoryData.effective_date) {
      setError('Please fill in all regulatory fields');
      return;
    }

    setActiveAnalysis('regulatory');
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await analysisAPI.simulateRegulatory(document.id, regulatoryData);
      if (response.success) {
        setResult(response.data);
        onAnalysisComplete(response.data);
      } else {
        setError(response.error || 'Regulatory analysis failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Regulatory analysis failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReputationAnalysis = async () => {
    setActiveAnalysis('reputation');
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await analysisAPI.analyzeReputation(document.id);
      if (response.success) {
        setResult(response.data);
        onAnalysisComplete(response.data);
      } else {
        setError(response.error || 'Reputation analysis failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Reputation analysis failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImpactAnalysis = async () => {
    if (!impactData.scenario || !impactData.timeframe) {
      setError('Please fill in all impact fields');
      return;
    }

    setActiveAnalysis('impact');
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await analysisAPI.analyzeImpact(document.id, impactData);
      if (response.success) {
        setResult(response.data);
        onAnalysisComplete(response.data);
      } else {
        setError(response.error || 'Impact analysis failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Impact analysis failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
      <h3>Analysis for {document.filename}</h3>
      
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={handleRiskAnalysis}
          disabled={isLoading}
          style={{
            margin: '5px',
            padding: '8px 16px',
            backgroundColor: isLoading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          Risk Assessment
        </button>
        
        <button
          onClick={handleReputationAnalysis}
          disabled={isLoading}
          style={{
            margin: '5px',
            padding: '8px 16px',
            backgroundColor: isLoading ? '#ccc' : '#28a745',
            color: 'white',
            border: 'none',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          Reputation Analysis
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h4>Regulatory Simulation</h4>
        <div style={{ marginBottom: '10px' }}>
          <input
            type="text"
            placeholder="Change Type"
            value={regulatoryData.change_type}
            onChange={(e) => setRegulatoryData({...regulatoryData, change_type: e.target.value})}
            style={{ width: '100%', padding: '8px', marginBottom: '5px', boxSizing: 'border-box' }}
          />
          <input
            type="text"
            placeholder="Description"
            value={regulatoryData.description}
            onChange={(e) => setRegulatoryData({...regulatoryData, description: e.target.value})}
            style={{ width: '100%', padding: '8px', marginBottom: '5px', boxSizing: 'border-box' }}
          />
          <input
            type="date"
            value={regulatoryData.effective_date}
            onChange={(e) => setRegulatoryData({...regulatoryData, effective_date: e.target.value})}
            style={{ width: '100%', padding: '8px', marginBottom: '10px', boxSizing: 'border-box' }}
          />
          <button
            onClick={handleRegulatoryAnalysis}
            disabled={isLoading}
            style={{
              padding: '8px 16px',
              backgroundColor: isLoading ? '#ccc' : '#ffc107',
              color: 'black',
              border: 'none',
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            Simulate Regulatory
          </button>
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h4>Impact Analysis</h4>
        <div style={{ marginBottom: '10px' }}>
          <input
            type="text"
            placeholder="Scenario"
            value={impactData.scenario}
            onChange={(e) => setImpactData({...impactData, scenario: e.target.value})}
            style={{ width: '100%', padding: '8px', marginBottom: '5px', boxSizing: 'border-box' }}
          />
          <input
            type="text"
            placeholder="Timeframe"
            value={impactData.timeframe}
            onChange={(e) => setImpactData({...impactData, timeframe: e.target.value})}
            style={{ width: '100%', padding: '8px', marginBottom: '10px', boxSizing: 'border-box' }}
          />
          <button
            onClick={handleImpactAnalysis}
            disabled={isLoading}
            style={{
              padding: '8px 16px',
              backgroundColor: isLoading ? '#ccc' : '#6f42c1',
              color: 'white',
              border: 'none',
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            Analyze Impact
          </button>
        </div>
      </div>

      {isLoading && <div>Running analysis...</div>}

      {error && (
        <div style={{ color: 'red', margin: '15px 0', padding: '10px', backgroundColor: '#ffebee' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
          <h4>Analysis Results</h4>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default AnalysisResult;
