import React, { useState } from 'react';
import { Info } from './icons';

/**
 * Contextual UI Tooltip Component
 * Accessible, tap & hover friendly explanation popup for technical & cryptographic elements.
 */
export default function Tooltip({ title, text, children, position = 'top', highlight }) {
  const [isVisible, setIsVisible] = useState(false);

  const getPositionClasses = () => {
    switch (position) {
      case 'bottom':
        return 'top-full left-1/2 -translate-x-1/2 mt-2';
      case 'left':
        return 'right-full top-1/2 -translate-y-1/2 mr-2';
      case 'right':
        return 'left-full top-1/2 -translate-y-1/2 ml-2';
      case 'top':
      default:
        return 'bottom-full left-1/2 -translate-x-1/2 mb-2';
    }
  };

  return (
    <div
      className="relative inline-flex items-center group/tooltip"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onClick={(e) => {
        e.stopPropagation();
        setIsVisible(!isVisible);
      }}
    >
      {children ? (
        children
      ) : (
        <button
          type="button"
          aria-label={title || "More information"}
          className="text-slate-400 hover:text-cyan-300 ml-1 transition-colors p-0.5 focus:outline-none"
        >
          <Info className="w-3.5 h-3.5 text-slate-400 hover:text-cyan-400" />
        </button>
      )}

      {isVisible && (
        <div
          role="tooltip"
          className={`absolute z-50 w-64 sm:w-72 max-w-[85vw] p-3 bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl shadow-2xl text-left pointer-events-none transition-all duration-150 animate-fade-in ${getPositionClasses()}`}
        >
          {title && (
            <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-800">
              <span className="text-xs font-bold text-white flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                <span>{title}</span>
              </span>
              {highlight && (
                <span className="text-[9px] font-mono font-semibold px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  {highlight}
                </span>
              )}
            </div>
          )}
          <p className="text-[11px] text-slate-300 leading-relaxed font-sans">{text}</p>
          <div className="mt-2 pt-1.5 border-t border-slate-800/80 text-[10px] text-slate-400 flex items-center justify-between">
            <span className="italic font-mono text-[9px] text-indigo-300">Nexus Guardrail</span>
            <span className="text-[9px] text-slate-400">Tap / hover to dismiss</span>
          </div>
        </div>
      )}
    </div>
  );
}
