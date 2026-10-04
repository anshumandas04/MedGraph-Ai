import React from 'react';
import { FlaskConical } from 'lucide-react';

export const PrototypeNotice: React.FC = () => {
  return (
    <div className="bg-slate-900 text-slate-50 px-4 py-2 flex items-center justify-center text-sm font-medium">
      <FlaskConical className="w-4 h-4 mr-2 text-primary-400" />
      Research prototype — Verify extracted records — Not for care decisions
    </div>
  );
};
