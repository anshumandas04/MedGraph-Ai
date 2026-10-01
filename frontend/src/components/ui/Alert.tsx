import React from 'react';
import { cn } from './Button';
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
}

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'info', title, children, ...props }, ref) => {
    const variants = {
      info: 'bg-blue-50 text-blue-900 border-blue-200',
      success: 'bg-emerald-50 text-emerald-900 border-emerald-200',
      warning: 'bg-amber-50 text-amber-900 border-amber-200',
      error: 'bg-red-50 text-red-900 border-red-200',
    };

    const icons = {
      info: <Info className="h-5 w-5 text-blue-600" />,
      success: <CheckCircle className="h-5 w-5 text-emerald-600" />,
      warning: <AlertTriangle className="h-5 w-5 text-amber-600" />,
      error: <AlertCircle className="h-5 w-5 text-red-600" />,
    };

    return (
      <div
        ref={ref}
        className={cn("relative w-full rounded-lg border p-4 flex gap-3", variants[variant], className)}
        {...props}
      >
        <div className="shrink-0">{icons[variant]}</div>
        <div>
          {title && <h5 className="mb-1 font-medium leading-none tracking-tight">{title}</h5>}
          <div className="text-sm opacity-90">{children}</div>
        </div>
      </div>
    );
  }
);
Alert.displayName = "Alert";
