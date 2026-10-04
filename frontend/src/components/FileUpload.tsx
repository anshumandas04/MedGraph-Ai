import React, { useCallback, useRef } from 'react';
import { UploadCloud } from 'lucide-react';

interface FileUploadProps {
  onFilesSelect: (files: File[]) => void;
  disabled?: boolean;
  accept?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFilesSelect, disabled = false, accept = ".pdf,.jpg,.jpeg,.png" }) => {
  const inputRef = useRef<HTMLInputElement>(null);

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled && e.dataTransfer.files.length > 0) {
      onFilesSelect(Array.from(e.dataTransfer.files));
    }
  }, [disabled, onFilesSelect]);

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelect(Array.from(e.target.files));
    }
    // Allow selecting the same file again after a failed upload.
    e.target.value = '';
  };

  return (
    <div 
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      onKeyDown={(e) => {
        if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      className={`border-2 border-dashed border-slate-300 rounded-lg p-8 text-center transition-colors ${disabled ? 'cursor-wait opacity-60' : 'hover:bg-slate-50 cursor-pointer'}`}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onClick={() => !disabled && inputRef.current?.click()}
    >
      <input 
        id="file-upload" 
        ref={inputRef}
        type="file" 
        className="hidden" 
        accept={accept}
        multiple
        disabled={disabled}
        onChange={handleFileInput}
      />
      <UploadCloud className="w-10 h-10 text-primary-500 mx-auto mb-4" />
      <h4 className="text-sm font-medium text-slate-900 mb-1">Click to choose files or drag and drop</h4>
      <p className="text-xs text-slate-500">Select or drop multiple PDF, JPG, or PNG files (max 50MB each)</p>
    </div>
  );
};
