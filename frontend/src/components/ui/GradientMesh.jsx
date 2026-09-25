import React from 'react';
import { cn } from '../../utils/cn';

export function GradientMesh({
  className,
  intensity = 'normal',
  children,
  fullscreen = false,
}) {
  const intensityMap = {
    subtle: 'opacity-25',
    normal: 'opacity-40',
    vibrant: 'opacity-60',
  };

  return (
    <div
      className={cn(
        'relative overflow-hidden',
        fullscreen ? 'fixed inset-0 pointer-events-none z-0' : '',
        className
      )}
    >
      {/* Background radial blobs */}
      <div
        className={cn(
          'absolute inset-0 pointer-events-none select-none transition-opacity duration-700',
          intensityMap[intensity] || intensityMap.normal
        )}
        aria-hidden="true"
      >
        {/* Blob 1: Teal primary blob (top-left) */}
        <div
          className="absolute -top-[15%] -left-[10%] w-[55vw] h-[55vw] max-w-[700px] max-h-[700px] rounded-full bg-[#0EA5B7]/40 blur-3xl animate-mesh-drift-1"
          style={{ willChange: 'transform' }}
        />

        {/* Blob 2: Secondary Blue blob (bottom-right) */}
        <div
          className="absolute -bottom-[20%] -right-[10%] w-[60vw] h-[60vw] max-w-[750px] max-h-[750px] rounded-full bg-[#3B82F6]/35 blur-3xl animate-mesh-drift-2"
          style={{ willChange: 'transform' }}
        />

        {/* Blob 3: Soft Cyan/Teal accent (center / floating) */}
        <div
          className="absolute top-[35%] right-[25%] w-[45vw] h-[45vw] max-w-[550px] max-h-[550px] rounded-full bg-cyan-400/25 blur-3xl animate-mesh-drift-3"
          style={{ willChange: 'transform' }}
        />

        {/* Subtle grid pattern overlay for precision medical aesthetic */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `radial-gradient(#0F172A 1px, transparent 1px)`,
            backgroundSize: '24px 24px',
          }}
        />
      </div>

      {/* Foreground content container */}
      {children && <div className="relative z-10">{children}</div>}
    </div>
  );
}

export default GradientMesh;
