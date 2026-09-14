import { useState, useEffect, useRef } from 'react';
import { generateCpuHistory, generateMemoryHistory, generateNetworkHistory } from '../utils/mockData';

interface DataPoint {
  time: string;
  [key: string]: number | string;
}

export function useRealTimeSeries(
  initialFn: () => DataPoint[],
  updateFn: (prev: DataPoint[]) => DataPoint[],
  interval = 2000,
  enabled = true
) {
  const [data, setData] = useState<DataPoint[]>(initialFn);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!enabled) return;
    intervalRef.current = setInterval(() => {
      setData(prev => updateFn(prev));
    }, interval);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [enabled, interval, updateFn]);

  return data;
}

/**
 * useCpuHistory — rolling 60-point CPU chart.
 * @param enabled - Whether to run the interval
 * @param seedValue - Current real CPU value to anchor the random walk
 */
export function useCpuHistory(enabled = true, seedValue?: number) {
  const [data, setData] = useState(() => {
    const seed = seedValue ?? 35;
    return generateCpuHistory(60, seed);
  });

  // When a real seedValue arrives for the first time, shift the last point to it
  const seededRef = useRef(false);
  useEffect(() => {
    if (!seededRef.current && seedValue !== undefined && seedValue > 0) {
      seededRef.current = true;
      setData(prev => {
        const now = new Date();
        const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        return [...prev.slice(1), { time, cpu: seedValue }];
      });
    }
  }, [seedValue]);

  useEffect(() => {
    if (!enabled) return;
    const interval = setInterval(() => {
      setData(prev => {
        const last = prev[prev.length - 1];
        const lastCpu = typeof last?.cpu === 'number' ? last.cpu : seedValue ?? 35;
        const newCpu = Math.max(5, Math.min(95, lastCpu + (Math.random() - 0.45) * 8));
        const now = new Date();
        const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        return [...prev.slice(1), { time, cpu: parseFloat(newCpu.toFixed(1)) }];
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [enabled, seedValue]);

  return data;
}

/**
 * useMemoryHistory — rolling 60-point Memory chart.
 * @param enabled - Whether to run the interval
 * @param seedValue - Current real memory % to anchor the random walk
 */
export function useMemoryHistory(enabled = true, seedValue?: number) {
  const [data, setData] = useState(() => {
    const seed = seedValue ?? 60;
    return generateMemoryHistory(60, seed);
  });

  const seededRef = useRef(false);
  useEffect(() => {
    if (!seededRef.current && seedValue !== undefined && seedValue > 0) {
      seededRef.current = true;
      setData(prev => {
        const now = new Date();
        const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        return [...prev.slice(1), { time, memory: seedValue }];
      });
    }
  }, [seedValue]);

  useEffect(() => {
    if (!enabled) return;
    const interval = setInterval(() => {
      setData(prev => {
        const last = prev[prev.length - 1];
        const lastMem = typeof last?.memory === 'number' ? last.memory : seedValue ?? 60;
        const newMem = Math.max(20, Math.min(90, lastMem + (Math.random() - 0.48) * 4));
        const now = new Date();
        const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        return [...prev.slice(1), { time, memory: parseFloat(newMem.toFixed(1)) }];
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [enabled, seedValue]);

  return data;
}

export function useNetworkHistory(enabled = true) {
  const [data, setData] = useState(() => generateNetworkHistory(60));

  useEffect(() => {
    if (!enabled) return;
    const interval = setInterval(() => {
      setData(prev => {
        const last = prev[prev.length - 1];
        const lastIn = typeof last?.inbound === 'number' ? last.inbound : 10;
        const lastOut = typeof last?.outbound === 'number' ? last.outbound : 3;
        const newIn = Math.max(0, lastIn + (Math.random() - 0.4) * 4);
        const newOut = Math.max(0, lastOut + (Math.random() - 0.4) * 2);
        const now = new Date();
        const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        return [...prev.slice(1), {
          time,
          inbound: parseFloat(newIn.toFixed(1)),
          outbound: parseFloat(newOut.toFixed(1)),
        }];
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [enabled]);

  return data;
}

export function useCounter(target: number, duration = 1500) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.floor(eased * target));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [target, duration]);

  return value;
}

export function useLocalStorage<T>(key: string, initial: T): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : initial;
    } catch {
      return initial;
    }
  });

  const set = (v: T) => {
    setValue(v);
    try {
      localStorage.setItem(key, JSON.stringify(v));
    } catch { /* ignore */ }
  };

  return [value, set];
}
