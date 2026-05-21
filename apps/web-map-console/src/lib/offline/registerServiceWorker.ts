/**
 * Service worker bootstrap.
 *
 * Web console pernah memasang service worker lama yang menyebabkan bundle JS
 * lama tetap di-serve setelah redeploy Cloud Run. Selama field-test rollout,
 * SW DINONAKTIFKAN dan bootstrap berikut justru aktif **mencabut** semua SW
 * yang sebelumnya terdaftar plus menghapus Cache Storage yang dipasangnya,
 * lalu reload sekali agar bundle baru terambil bersih.
 */
export function registerServiceWorker(): void {
  if (typeof window === "undefined" || typeof navigator === "undefined") return;
  if (!("serviceWorker" in navigator)) return;

  navigator.serviceWorker
    .getRegistrations()
    .then((regs) => {
      if (regs.length === 0) return false;
      return Promise.all(regs.map((r) => r.unregister())).then((results) =>
        results.some(Boolean)
      );
    })
    .then((unregistered) => {
      if (typeof caches !== "undefined" && caches?.keys) {
        return caches.keys().then((keys) =>
          Promise.all(keys.map((k) => caches.delete(k))).then(() => unregistered)
        );
      }
      return unregistered;
    })
    .then((needsReload) => {
      if (!needsReload) return;
      if (sessionStorage.getItem("__sw_killswitch_reloaded__")) return;
      sessionStorage.setItem("__sw_killswitch_reloaded__", "1");
      window.location.reload();
    })
    .catch(() => {
      /* tidak boleh mengganggu UI */
    });
}
