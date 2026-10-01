import React, { useCallback } from 'react';
import { UploadCloud } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, accept = ".pdf,.jpg,.jpeg,.png" }) => {
  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  }, [onFileSelect]);

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div 
      className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:bg-slate-50 transition-colors cursor-pointer"
      onDrop={onDrop}
      onDragOver={onDragOver}
      onClick={() => document.getElementById('file-upload')?.click()}
    >
      <input 
        id="file-upload" 
        type="file" 
        className="hidden" 
        accept={accept}
        onChange={handleFileInput}
      />
      <UploadCloud className="w-10 h-10 text-primary-500 mx-auto mb-4" />
      <h4 className="text-sm font-medium text-slate-900 mb-1">Click to upload or drag and drop</h4>
      <p className="text-xs text-slate-500">PDF, JPG, PNG (Max 10MB)</p>
    </div>
  );
};
