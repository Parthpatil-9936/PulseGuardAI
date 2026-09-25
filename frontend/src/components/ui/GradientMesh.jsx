import React from 'react';

/**
 * GradientMesh: Animated soft teal-to-blue radial mesh background
 * Soft blurred blobs with low opacity and animated drift keyframes.
 */
export const GradientMesh = ({ children, className = '' }) => {
  return (
    <div className={`relative overflow-hidden bg-base-background min-h-screen ${className}`}>
      {/* Animated Mesh Blobs */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
        {/* Teal blob - top left */}
        <div 
          className="absolute -top-[15%] -left-[10%] w-[550px] h-[550px] rounded-full bg-primary-500/15 blur-[120px] animate-mesh-drift"
          style={{ animationDuration: '22s' }}
        />
        {/* Blue blob - top right */}
        <div 
          className="absolute top-[5%] -right-[15%] w-[600px] h-[600px] rounded-full bg-secondary-500/12 blur-[130px] animate-mesh-drift"
          style={{ animationDuration: '28s', animationDirection: 'reverse' }}
        />
        {/* Cyan/teal accent blob - bottom center */}
        <div 
          className="absolute -bottom-[20%] left-[20%] w-[700px] h-[600px] rounded-full bg-teal-400/15 blur-[140px] animate-mesh-drift"
          style={{ animationDuration: '25s' }}
        />
        {/* Subtle grid pattern overlay for clean medical/tech texture */}
        <div 
          className="absolute inset-0 opacity-[0.03] bg-[radial-gradient(#0EA5B7_1px,transparent_1px)] [background-size:24px_24px]"
        />
      </div>

      {/* Content wrapper */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default GradientMesh;
