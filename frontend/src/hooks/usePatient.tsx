import React, { createContext, useContext, useState, useEffect } from 'react';
import { patientsService } from '../services/patients';
import { Patient } from '../types';

interface PatientContextType {
  selectedPatientId: string | null;
  selectedPatient: Patient | null;
  selectPatient: (id: string) => void;
  isLoading: boolean;
}

const PatientContext = createContext<PatientContextType | undefined>(undefined);

export const PatientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(localStorage.getItem('selectedPatientId'));
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (selectedPatientId) {
      setIsLoading(true);
      patientsService.getPatient(selectedPatientId)
        .then(setSelectedPatient)
        .catch(() => {
          setSelectedPatientId(null);
          localStorage.removeItem('selectedPatientId');
        })
        .finally(() => setIsLoading(false));
    } else {
      setSelectedPatient(null);
      // Try to auto-select demo patient
      patientsService.getPatients().then(patients => {
        if (patients.length > 0) {
          selectPatient(patients[0].id);
        }
      });
    }
  }, [selectedPatientId]);

  const selectPatient = (id: string) => {
    setSelectedPatientId(id);
    localStorage.setItem('selectedPatientId', id);
  };

  return (
    <PatientContext.Provider value={{ selectedPatientId, selectedPatient, selectPatient, isLoading }}>
      {children}
    </PatientContext.Provider>
  );
};

export const usePatient = () => {
  const context = useContext(PatientContext);
  if (context === undefined) {
    throw new Error('usePatient must be used within a PatientProvider');
  }
  return context;
};
