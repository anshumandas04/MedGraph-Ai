import React from 'react';
import { Outlet } from 'react-router-dom';
import { PrototypeNotice } from '../components/PrototypeNotice';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <PrototypeNotice />
      <div className="flex-1 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-slate-900">
            MedGraph
          </h2>
          <p className="mt-2 text-center text-sm text-slate-600">
            Intelligent Medical History Timeline
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
};
