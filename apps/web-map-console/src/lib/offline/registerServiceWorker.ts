/**
 * Service worker bootstrap.
 *
 * Dua mode:
 *
 *   1. KILL-SWITCH (default): cabut SW lama + clear Cache Storage + reload sekali.
 *      Dipakai saat rollout sehingga bundle lama tidak menahan.
 *
 *   2. REGISTER (opt-in via VITE_ENABLE_SERVICE_WORKER=true): setelah SW lama
 *      dicabut, daftarkan SW baru `/service-worker.js` (versi safe yang
 *      melewatkan PMTiles dan response 206).
 *
 * Mode ditentukan di build time lewat env. Saat field-test rollout, biarkan
 * default (kill-switch) sampai SW baru terbukti aman.
 */
export function registerServiceWorker(): void {
  if (typeof window === "undefined" || typeof navigator === "undefined") return;
  if (!("serviceWorker" in navigator)) return;

  const enable = import.meta.env.VITE_ENABLE_SERVICE_WORKER === "true";
  const swPath = import.meta.env.VITE_SERVICE_WORKER_PATH ?? "/service-worker.js";

  const purgeLegacy = navigator.serviceWorker
    .getRegistrations()
    .then(async (regs) => {
      // Cabut HANYA SW yang scope-nya BUKAN target sekarang (alias SW lama).
      let cabutAda = false;
      for (const reg of regs) {
        const scriptURL = reg.active?.scriptURL ?? "";
        if (!scriptURL.endsWith(swPath)) {
          await reg.unregister();
          cabutAda = true;
        }
      }
      return cabutAda;
    })
    .then(async (cabutAda) => {
      if (cabutAda && typeof caches !== "undefined" && caches?.keys) {
        const keys = await caches.keys();
        // Bersihkan cache lama yang tidak diawali nama target.
        await Promise.all(
          keys
            .filter((k) => !k.startsWith("time-rally-web-console-v"))
            .map((k) => caches.delete(k))
        );
      }
      return cabutAda;
    })
    .then((cabutAda) => {
      if (cabutAda && !sessionStorage.getItem("__sw_killswitch_reloaded__")) {
        sessionStorage.setItem("__sw_killswitch_reloaded__", "1");
        window.location.reload();
      }
    })
    .catch(() => {
      /* tidak boleh mengganggu UI */
    });

  if (!enable) {
    return;
  }

  // Daftar SW baru setelah kill-switch SW lama selesai.
  purgeLegacy
    .then(() => navigator.serviceWorker.register(swPath, { scope: "/" }))
    .catch(() => {
      /* register gagal -> lanjut tanpa SW */
    });
}
