/**
 * Optional Sentry bootstrap untuk frontend.
 *
 * `@sentry/react` adalah optional dependency. Kalau modul tidak terinstall,
 * fungsi `initSentry` no-op sehingga build/dev tidak terganggu.
 *
 * Untuk mengaktifkan:
 *   npm install @sentry/react
 *   set VITE_SENTRY_DSN di .env.production
 */

export interface SentryBootstrapOptions {
  dsn?: string;
  environment?: string;
  tracesSampleRate?: number;
  release?: string;
}

type SentryReactModule = {
  init: (options: {
    dsn: string;
    environment: string;
    tracesSampleRate: number;
    release: string;
  }) => void;
};

const optionalImport = new Function("specifier", "return import(specifier)") as (
  specifier: string
) => Promise<SentryReactModule>;

export async function initSentry(options: SentryBootstrapOptions = {}): Promise<boolean> {
  const dsn = options.dsn ?? import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) return false;
  try {
    const Sentry = await optionalImport("@sentry/react");
    Sentry.init({
      dsn,
      environment: options.environment ?? import.meta.env.VITE_SENTRY_ENVIRONMENT ?? "production",
      tracesSampleRate:
        options.tracesSampleRate ??
        Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE ?? 0.05),
      release: options.release ?? `time-rally-web@${import.meta.env.MODE}`,
    });
    return true;
  } catch {
    return false;
  }
}
