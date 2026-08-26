import React, { useEffect, useState } from 'react';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import CasesList from './components/CasesList';
import TroubleshootView from './components/TroubleshootView';
import HumanReviewView from './components/HumanReviewView';
import RuleCheckerView from './components/RuleCheckerView';
import ResponsibleAILog from './components/ResponsibleAILog';
import { checkHealth } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedCaseId, setSelectedCaseId] = useState('CASE-VLAN-001');
  const [health, setHealth] = useState(null);

  useEffect(() => {
    async function loadHealth() {
      try {
        const h = await checkHealth();
        setHealth(h);
      } catch (err) {
        console.error(err);
      }
    }
    loadHealth();
  }, []);

  const handleSelectCaseForTroubleshoot = (caseId) => {
    setSelectedCaseId(caseId);
    setActiveTab('troubleshoot');
  };

  const handleNavigateToReview = (caseId) => {
    setSelectedCaseId(caseId);
    setActiveTab('review');
  };

  return (
    <div className="min-h-screen w-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased">
      {/* Navigation Header */}
      <Navigation 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        health={health} 
      />

      {/* Main Tab Content */}
      <main className="flex-1 w-full pb-12">
        {activeTab === 'dashboard' && (
          <Dashboard onNavigateToCase={handleSelectCaseForTroubleshoot} />
        )}
        {activeTab === 'cases' && (
          <CasesList onSelectCase={handleSelectCaseForTroubleshoot} />
        )}
        {activeTab === 'troubleshoot' && (
          <TroubleshootView 
            selectedCaseId={selectedCaseId} 
            onNavigateToReview={handleNavigateToReview}
          />
        )}
        {activeTab === 'review' && (
          <HumanReviewView 
            selectedCaseId={selectedCaseId} 
          />
        )}
        {activeTab === 'rules' && (
          <RuleCheckerView onSelectCase={handleSelectCaseForTroubleshoot} />
        )}
        {activeTab === 'responsible-ai' && (
          <ResponsibleAILog />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-3 px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <span>Cisco NetSage AI &bull; Packet Tracer Troubleshooting Assistant</span>
        <span className="text-[11px] text-slate-600">
          Deterministic Python Rules &bull; Mandatory Human-in-the-Loop Review &bull; Responsible AI
        </span>
      </footer>
    </div>
  );
}
