export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'PATIENT' | 'CAREGIVER' | 'CLINICIAN' | 'ADMIN';
  is_active: boolean;
  created_at: string;
}

export interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  medical_record_number: string;
  created_at: string;
}

export interface PatientSummary {
  id: string;
  name: string;
  document_count: number;
  event_count: number;
  open_signals: number;
  medication_count: number;
  investigation_count: number;
}

export interface Document {
  id: string;
  patient_id: string;
  original_filename: string;
  document_type: string;
  document_date: string | null;
  processing_status: 'UPLOADED' | 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  file_size: number;
  created_at: string;
}

export interface DocumentDetail extends Document {
  pages: DocumentPage[];
}

export interface DocumentPage {
  id: string;
  page_number: number;
  text_content: string | null;
  ocr_confidence: number | null;
}

export interface HealthEvent {
  id: string;
  patient_id: string;
  event_type: string;
  event_date: string | null;
  title: string;
  description: string | null;
  confidence: number;
  source_document_id: string | null;
  source_page: number | null;
  source_excerpt: string | null;
  value: string | null;
  unit: string | null;
  entity_name: string | null;
  status: string | null;
  relationships?: EventRelationship[];
}

export interface EventRelationship {
  id: string;
  source_event_id: string;
  target_event_id: string;
  relationship_type: string;
  confidence: number;
}

export interface TimelineEntry {
  date: string;
  events: HealthEvent[];
}

export interface Signal {
  id: string;
  patient_id: string;
  signal_type: string;
  title: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  confidence: number;
  status: 'OPEN' | 'VERIFIED' | 'DISMISSED' | 'NEEDS_VERIFICATION';
  evidence: SignalEvidence[];
  created_at: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_comment?: string;
}

export interface SignalEvidence {
  id: string;
  signal_id: string;
  event_id: string | null;
  document_id: string | null;
  page_number: number | null;
  excerpt: string | null;
  role: 'SUPPORTING' | 'CONFLICTING' | 'CONTEXT';
  document_filename?: string;
  event_title?: string;
}

export interface Medication {
  id: string;
  patient_id: string;
  name: string;
  generic_name: string | null;
  dosage: string | null;
  frequency: string | null;
  route: string | null;
  status: 'ACTIVE' | 'DISCONTINUED' | 'CHANGED' | 'UNKNOWN';
  start_date: string | null;
  end_date: string | null;
  events: MedicationEventItem[];
}

export interface MedicationEventItem {
  date: string | null;
  action: string;
  event_id: string;
  document_id: string | null;
}

export interface Investigation {
  id: string;
  patient_id: string;
  name: string;
  category: string;
  results: InvestigationResult[];
}

export interface InvestigationResult {
  id: string;
  value: string | null;
  unit: string | null;
  reference_range: string | null;
  is_abnormal: boolean | null;
  test_date: string | null;
  event_id: string;
}

export interface SearchResponse {
  answer: string;
  citations: Citation[];
  related_events: HealthEvent[];
}

export interface Citation {
  document_id: string;
  document_name: string;
  page_number: number;
  excerpt: string;
  confidence: number;
}

export interface DashboardData {
  total_documents: number;
  total_events: number;
  open_signals: number;
  total_medications: number;
  total_investigations: number;
  recent_documents: Document[];
  recent_signals: Signal[];
}

export interface ResearchDashboard {
  documents_processed: number;
  events_extracted: number;
  signals_generated: number;
  signals_verified: number;
  signals_dismissed: number;
  avg_confidence: number;
  signal_distribution: Record<string, number>;
  processing_failures: number;
}

export interface EvaluationResult {
  precision: number;
  recall: number;
  f1: number;
  false_positive_rate: number;
  evidence_accuracy: number;
  details: EvaluationDetail[];
}

export interface EvaluationDetail {
  test_case: string;
  expected: string;
  predicted: string;
  correct: boolean;
  evidence: string;
  confidence: number;
}
