import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsService } from '../services/documents';
import { usePatient } from '../hooks/usePatient';
import { FileUpload } from '../components/FileUpload';
import { Link } from 'react-router-dom';
import { FileText, Clock, AlertCircle, CheckCircle, Trash2, RotateCw } from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';
import { Button } from '../components/ui/Button';

interface UploadItem {
  id: string;
  file: File;
  status: 'QUEUED' | 'UPLOADING' | 'UPLOADED' | 'FAILED';
}

export const DocumentsPage: React.FC = () => {
  const { selectedPatientId } = usePatient();
  const queryClient = useQueryClient();
  const [uploadItems, setUploadItems] = useState<UploadItem[]>([]);
  const [reprocessProgress, setReprocessProgress] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents', selectedPatientId],
    queryFn: () => documentsService.getDocuments(selectedPatientId!),
    enabled: !!selectedPatientId,
    refetchInterval: (query) => query.state.data?.some((doc) => ['UPLOADED', 'QUEUED', 'PROCESSING'].includes(doc.processing_status)) ? 2000 : false,
  });

  const uploadMutation = useMutation({
    mutationFn: async (files: Array<{ id: string; file: File }>) => {
      // Upload one file at a time so a large selection does not overload the OCR worker.
      for (const item of files) {
        setUploadItems((current) => current.map((upload) =>
          upload.id === item.id ? { ...upload, status: 'UPLOADING' } : upload
        ));
        try {
          await documentsService.uploadDocument(selectedPatientId!, item.file);
          setUploadItems((current) => current.map((upload) =>
            upload.id === item.id ? { ...upload, status: 'UPLOADED' } : upload
          ));
        } catch {
          setUploadItems((current) => current.map((upload) =>
            upload.id === item.id ? { ...upload, status: 'FAILED' } : upload
          ));
        }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', selectedPatientId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => documentsService.deleteDocument(documentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
    },
  });

  const reprocessMutation = useMutation({
    mutationFn: async (documents: Array<{ id: string; original_filename: string }>) => {
      let completed = 0;
      const failed: string[] = [];
      for (const document of documents) {
        setReprocessProgress('Reprocessing ' + (completed + failed.length + 1) + ' of ' + documents.length + ': ' + document.original_filename);
        try {
          await documentsService.reprocessDocument(document.id);
          completed += 1;
        } catch {
          failed.push(document.original_filename);
        }
      }
      return { completed, failed };
    },
    onSuccess: async ({ completed, failed }) => {
      setReprocessProgress(failed.length ? completed + ' queued; ' + failed.length + ' failed. Check Diagnostics.' : completed + ' documents reprocessed.');
      await queryClient.invalidateQueries();
    },
    onError: () => setReprocessProgress('Reprocessing did not complete. Check Diagnostics for the request ID and backend error.'),
  });

  const handleFilesSelect = (files: File[]) => {
    const batch = files.map((file) => ({ id: crypto.randomUUID(), file }));
    setUploadItems(batch.map(({ id, file }) => ({ id, file, status: 'QUEUED' })));
    uploadMutation.mutate(batch);
  };

  const handleDelete = (documentId: string, filename: string) => {
    const confirmed = window.confirm(
      `Permanently delete “${filename}”? The uploaded file, extracted text, events, search content, and related generated records will also be removed.`
    );
    if (confirmed) deleteMutation.mutate(documentId);
  };

  const handleReprocessAll = () => {
    const eligible = (data ?? []).filter((doc) => ['COMPLETED', 'FAILED', 'NEEDS_REVIEW'].includes(doc.processing_status));
    if (!eligible.length) return;
    const confirmed = window.confirm(
      'Reprocess ' + eligible.length + ' documents with the currently configured OCR and AI providers? This rebuilds the extracted records for those documents. If an external AI provider is configured, document text will be sent to that provider.'
    );
    if (confirmed) {
      setReprocessProgress('Starting reprocessing…');
      reprocessMutation.mutate(eligible.map(({ id, original_filename }) => ({ id, original_filename })));
    }
  };

  if (!selectedPatientId) return <div>Select a patient</div>;
  if (isLoading) return <div className="space-y-4 p-6"><Skeleton className="h-16 w-full" /><Skeleton className="h-16 w-full" /></div>;
  if (error || !data) return <ErrorState error={error} />;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case 'FAILED': return <AlertCircle className="w-5 h-5 text-red-500" />;
      default: return <Clock className="w-5 h-5 text-amber-500" />;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Documents</h2>
        <Button variant="outline" size="sm" onClick={handleReprocessAll} disabled={reprocessMutation.isPending || !data.some((doc) => ['COMPLETED', 'FAILED', 'NEEDS_REVIEW'].includes(doc.processing_status))}>
          <RotateCw className="mr-2 h-4 w-4" />
          {reprocessMutation.isPending ? 'Reprocessing…' : 'Reprocess existing'}
        </Button>
      </div>

      {reprocessProgress && <p role="status" className="text-sm text-slate-600">{reprocessProgress}</p>}

      <FileUpload onFilesSelect={handleFilesSelect} disabled={uploadMutation.isPending} />
      {deleteMutation.isError && (
        <div role="alert" className="text-sm text-red-700">Could not remove this document. It may already have been removed, or the server could not clean up its stored file.</div>
      )}
      {uploadItems.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-4" aria-live="polite">
          <div className="mb-3 text-sm font-medium text-slate-800">
            {uploadMutation.isPending
              ? `Uploading ${uploadItems.findIndex((item) => item.status === 'UPLOADING') + 1} of ${uploadItems.length}…`
              : `Upload complete: ${uploadItems.filter((item) => item.status === 'UPLOADED').length} uploaded, ${uploadItems.filter((item) => item.status === 'FAILED').length} failed`}
          </div>
          <ul className="space-y-2">
            {uploadItems.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-4 text-sm">
                <span className="truncate text-slate-700">{item.file.name}</span>
                <span className={`shrink-0 ${item.status === 'FAILED' ? 'text-red-700' : item.status === 'UPLOADED' ? 'text-emerald-700' : 'text-slate-500'}`}>
                  {item.status === 'QUEUED' ? 'Waiting…' : item.status === 'UPLOADING' ? 'Uploading…' : item.status === 'UPLOADED' ? 'Uploaded; processing queued' : 'Upload failed'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">File Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Type / Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Size</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {data.map((doc) => (
              <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link to={`/app/documents/${doc.id}`} className="flex items-center text-primary-600 hover:underline">
                    <FileText className="w-5 h-5 mr-3 text-slate-400" />
                    <span className="font-medium">{doc.original_filename}</span>
                  </Link>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                  {doc.document_type}
                  {doc.document_date && <div className="text-xs">{doc.document_date}</div>}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(doc.processing_status)}
                    <span className="text-sm font-medium text-slate-700">{doc.processing_status}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                  {(doc.file_size / 1024).toFixed(1)} KB
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <button
                    type="button"
                    onClick={() => handleDelete(doc.id, doc.original_filename)}
                    disabled={deleteMutation.isPending}
                    aria-label={`Delete ${doc.original_filename}`}
                    className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-wait disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" />
                    {deleteMutation.isPending && deleteMutation.variables === doc.id ? 'Removing…' : 'Remove'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data.length === 0 && (
          <div className="p-12 text-center text-slate-500">No documents found.</div>
        )}
      </div>
    </div>
  );
};
