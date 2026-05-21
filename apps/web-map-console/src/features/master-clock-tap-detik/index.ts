/**
 * Master clock tap-detik feature.
 *
 * Membantu navigator menjalankan jam reli berbasis "tap detik" - setiap tap
 * akan mengunci jam ke detik bulat sehingga ETA dapat dihitung presisi.
 */

export interface MasterClockState {
  rallyStart: number; // epoch ms
  masterOffsetMs: number; // offset terhadap device clock
  ticking: boolean;
  lastTap: number | null;
}

export function startClock(rallyStartIso: string): MasterClockState {
  const start = new Date(rallyStartIso).getTime();
  const now = Date.now();
  return {
    rallyStart: start,
    masterOffsetMs: 0,
    ticking: true,
    lastTap: null,
  };
}

export function tapDetik(state: MasterClockState, expectedSecond?: number): MasterClockState {
  const now = Date.now();
  if (expectedSecond === undefined) {
    return { ...state, lastTap: now };
  }
  // Snap ke detik bulat target (expectedSecond detik setelah rally start)
  const targetMs = state.rallyStart + expectedSecond * 1000;
  return { ...state, lastTap: now, masterOffsetMs: targetMs - now };
}

export function clockReading(state: MasterClockState): { masterTimeMs: number; iso: string } {
  const masterTimeMs = Date.now() + state.masterOffsetMs;
  return { masterTimeMs, iso: new Date(masterTimeMs).toISOString() };
}

export function elapsedSeconds(state: MasterClockState): number {
  return Math.max(0, Math.floor((Date.now() + state.masterOffsetMs - state.rallyStart) / 1000));
}
