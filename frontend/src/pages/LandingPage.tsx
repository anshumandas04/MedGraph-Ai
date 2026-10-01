import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-slate-900">MedGraph</h1>
          <div className="flex gap-4">
            <Link to="/login"><Button variant="ghost">Log in</Button></Link>
            <Link to="/register"><Button>Sign up</Button></Link>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h2 className="text-5xl font-extrabold text-slate-900 tracking-tight mb-6">
            Intelligent Medical History Timeline
          </h2>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto mb-10">
            MedGraph uses advanced LLMs to extract, structure, and visualize complex medical histories from raw documents.
          </p>
          <Link to="/login"><Button size="lg" className="text-lg px-10">Explore Demo</Button></Link>
        </div>
        
        <div className="mt-24 grid md:grid-cols-3 gap-12">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-xl font-bold mb-3">1. Upload Documents</h3>
            <p className="text-slate-600">Upload raw PDFs, clinical notes, and lab results.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-xl font-bold mb-3">2. Extract Entities</h3>
            <p className="text-slate-600">LLM pipeline extracts events, medications, and relationships.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-xl font-bold mb-3">3. Visualize Timeline</h3>
            <p className="text-slate-600">Explore a clean, chronological view of the patient's history.</p>
          </div>
        </div>
      </main>
    </div>
  );
};
