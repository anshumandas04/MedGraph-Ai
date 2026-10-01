import React from 'react';
import { cn } from './Button';

export const Skeleton = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => {
  return (
    <div className={cn("animate-pulse rounded-md bg-slate-200", className)} {...props} />
  );
};
