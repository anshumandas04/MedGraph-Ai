import React, { createContext, useContext, useEffect, useState } from 'react';
import { patientsService } from '../services/patients';
import { Patient } from '../types';
import { useAuth } from './useAuth';

interface PatientContextType {
  availablePatients: Patient[];
  selectedPatientId: string | null;
  selectedPatient: Patient | null;
  selectPatient: (id: string) => void;
  createMyProfile: (data: {
    first_name: string;
    last_name: string;
    date_of_birth: string;
    gender: string;
  }) => Promise<void>;
  needsProfile: boolean;
  loadError: string | null;
  isLoading: boolean;
}

const PatientContext = createContext<PatientContextType | undefined>(undefined);

const storageKey = (userId: string) => `selectedPatientId:${userId}`;

export const PatientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [availablePatients, setAvailablePatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [needsProfile, setNeedsProfile] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;

    if (!user) {
      setAvailablePatients([]);
      setSelectedPatientId(null);
      setNeedsProfile(false);
      setLoadError(null);
      setIsLoading(false);
      return () => { active = false; };
    }

    setIsLoading(true);
    setLoadError(null);
    setNeedsProfile(false);
    setAvailablePatients([]);
    setSelectedPatientId(null);
    // Remove the old shared key so another account in this browser cannot inherit its selection.
    localStorage.removeItem('selectedPatientId');

    patientsService.getPatients()
      .then((patients) => {
        if (!active) return;
        setAvailablePatients(patients);

        if (user.role === 'PATIENT') {
          localStorage.removeItem(storageKey(user.id));
          if (patients.length === 1) {
            setSelectedPatientId(patients[0].id);
          } else if (patients.length === 0) {
            setNeedsProfile(true);
          } else {
            setLoadError('More than one patient profile is linked to this account. Please contact an administrator.');
          }
          return;
        }

        const savedId = localStorage.getItem(storageKey(user.id));
        const selected = patients.find((patient) => patient.id === savedId) ?? patients[0];
        if (selected) setSelectedPatientId(selected.id);
      })
      .catch(() => {
        if (active) setLoadError('Could not load patient records. Please refresh and try again.');
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => { active = false; };
  }, [user?.id, user?.role]);

  const selectedPatient = availablePatients.find((patient) => patient.id === selectedPatientId) ?? null;

  const selectPatient = (id: string) => {
    if (!user || user.role === 'PATIENT' || !availablePatients.some((patient) => patient.id === id)) return;
    setSelectedPatientId(id);
    localStorage.setItem(storageKey(user.id), id);
  };

  const createMyProfile = async (data: {
    first_name: string;
    last_name: string;
    date_of_birth: string;
    gender: string;
  }) => {
    const patient = await patientsService.createMyProfile(data);
    setAvailablePatients([patient]);
    setSelectedPatientId(patient.id);
    setNeedsProfile(false);
    setLoadError(null);
  };

  return (
    <PatientContext.Provider value={{
      availablePatients,
      selectedPatientId,
      selectedPatient,
      selectPatient,
      createMyProfile,
      needsProfile,
      loadError,
      isLoading,
    }}>
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
