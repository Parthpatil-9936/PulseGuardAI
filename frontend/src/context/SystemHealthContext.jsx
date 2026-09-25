import React, { createContext, useContext, useState, useEffect } from 'react';

const SystemHealthContext = createContext(null);

export const SystemHealthProvider = ({ children }) => {
  const [isCloudOutage, setIsCloudOutage] = useState(false);
  const [muteRemainingSeconds, setMuteRemainingSeconds] = useState(0); // 0 = unmuted, max 300
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [latencyMs, setLatencyMs] = useState(3.4); // Edge ML target <5ms

  // Service health states
  const [services, setServices] = useState({
    fastApi: { name: 'FastAPI Edge Gateway', port: ':8000', status: 'healthy', latency: '2.1ms' },
    redis: { name: 'Redis Volatile FIFO Buffer', port: ':6379', status: 'healthy', memory: '14.2MB' },
    postgres: { name: 'PostgreSQL Audit Ledger', port: ':5432', status: 'healthy', chain: 'Verified' },
    webSocket: { name: 'Live Telemetry WebSocket', port: ':8000/ws', status: 'healthy', rate: '1 Hz' },
    mlEngine: { name: 'ML Triage Engine (1D-CNN)', port: 'Local Edge', status: 'healthy', inference: '3.4ms' },
    cloudSync: { name: 'Hospital WAN Cloud Sync', port: 'WAN Gateway', status: 'healthy', queue: '0 pkts' },
  });

  // Toggle Cloud Outage
  const toggleCloudOutage = () => {
    setIsCloudOutage(prev => {
      const next = !prev;
      setServices(s => ({
        ...s,
        cloudSync: {
          ...s.cloudSync,
          status: next ? 'offline' : 'healthy',
          queue: next ? '24 queued' : '0 pkts'
        }
      }));
      return next;
    });
  };

  // Mute Alarm with 300s clamp
  const toggleMute = () => {
    if (isAudioMuted) {
      setIsAudioMuted(false);
      setMuteRemainingSeconds(0);
    } else {
      setIsAudioMuted(true);
      setMuteRemainingSeconds(300); // 5 minutes anti-tamper clamp
    }
  };

  // Countdown timer for mute clamping
  useEffect(() => {
    if (!isAudioMuted || muteRemainingSeconds <= 0) {
      if (muteRemainingSeconds === 0 && isAudioMuted) {
        setIsAudioMuted(false);
      }
      return;
    }

    const timer = setInterval(() => {
      setMuteRemainingSeconds(sec => {
        if (sec <= 1) {
          setIsAudioMuted(false);
          return 0;
        }
        return sec - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isAudioMuted, muteRemainingSeconds]);

  // Subtle latency jitter
  useEffect(() => {
    const jitter = setInterval(() => {
      setLatencyMs((3.2 + Math.random() * 0.8).toFixed(1));
    }, 3000);
    return () => clearInterval(jitter);
  }, []);

  return (
    <SystemHealthContext.Provider value={{
      isCloudOutage,
      toggleCloudOutage,
      isAudioMuted,
      muteRemainingSeconds,
      toggleMute,
      services,
      latencyMs
    }}>
      {children}
    </SystemHealthContext.Provider>
  );
};

export const useSystemHealth = () => {
  const context = useContext(SystemHealthContext);
  if (!context) {
    throw new Error('useSystemHealth must be used within a SystemHealthProvider');
  }
  return context;
};

export default SystemHealthContext;
