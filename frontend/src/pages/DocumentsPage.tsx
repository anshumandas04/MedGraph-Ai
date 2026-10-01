import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsService } from '../services/documents';
import { usePatient } from '../hooks/usePatient';
import { FileUpload } from '../components/FileUpload';
import { Badge } from '../components/ui/Badge';
import { Link } from 'react-router-dom';
import { FileText, Clock, AlertCircle, CheckCircle } from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';

export const DocumentsPage: React.FC = () => {
  const { selectedPatientId } = usePatient();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents', selectedPatientId],
    queryFn: () => documentsService.getDocuments(selectedPatientId!),
    enabled: !!selectedPatientId,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentsService.uploadDocument(selectedPatientId!, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', selectedPatientId] });
    },
  });

  if (!selectedPatientId) return <div>Select a patient</div>;
  if (isLoading) return <div className="space-y-4 p-6"><Skeleton className="h-16 w-full" /><Skeleton className="h-16 w-full" /></div>;
  if (error || !data) return <ErrorState />;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case 'FAILED': return <AlertCircle className="w-5 h-5 text-red-500" />;
      default: return <Clock className="w-5 h-5 text-amber-500" />;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Documents</h2>
      </div>

      <FileUpload onFileSelect={(file) => uploadMutation.mutate(file)} />

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">File Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Type / Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Size</th>
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
