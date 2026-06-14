import React, { type InputHTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface AuthInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const AuthInput = React.forwardRef<HTMLInputElement, AuthInputProps>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div className="flex flex-col w-full">
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5 ml-1">
          {label}
        </label>
        <input
          ref={ref}
          className={twMerge(clsx(
            "w-full h-12 px-4 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 outline-none transition-all duration-300 shadow-sm dark:shadow-none",
            "focus:bg-white dark:focus:bg-white/10 focus:border-primary-500 focus:ring-1 focus:ring-primary-500",
            error && "border-red-500 focus:border-red-500 focus:ring-red-500",
            className
          ))}
          {...props}
        />
        {/* Error container with fixed height to prevent layout shift */}
        <div className="h-6 mt-1 flex items-start ml-1">
          <span
            className={twMerge(clsx(
              "text-xs text-red-500 dark:text-red-400 transition-opacity duration-300",
              error ? "opacity-100" : "opacity-0"
            ))}
          >
            {error || " "}
          </span>
        </div>
      </div>
    );
  }
);
AuthInput.displayName = 'AuthInput';
