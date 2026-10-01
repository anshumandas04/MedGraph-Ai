import React from 'react';
import { FileText } from 'lucide-react';
import { Link } from 'react-router-dom';

interface EvidenceItemProps {
  documentId: string;
  page: number | null;
  excerpt: string | null;
}

export const EvidenceItem: React.FC<EvidenceItemProps> = ({ documentId, page, excerpt }) => {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-md p-3 text-sm">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="w-4 h-4 text-slate-400" />
        <Link to={`/app/documents/${documentId}`} className="text-primary-600 hover:underline font-medium">
          Source Document {page ? `(Page ${page})` : ''}
        </Link>
      </div>
      {excerpt && (
        <blockquote className="border-l-2 border-slate-300 pl-3 italic text-slate-600 text-xs">
          "{excerpt}"
        </blockquote>
      )}
    </div>
  );
};
