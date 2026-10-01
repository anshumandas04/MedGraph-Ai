import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from './ui/Button';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ 
  title = "Something went wrong", 
  message = "We couldn't load the requested data.", 
  onRetry 
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="rounded-full bg-red-50 p-4 mb-4 text-red-500">
        <AlertCircle className="w-8 h-8" />
      </div>
      <h3 className="text-lg font-medium text-slate-900 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 mb-6 max-w-sm">{message}</p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline">Try Again</Button>
      )}
    </div>
  );
};
