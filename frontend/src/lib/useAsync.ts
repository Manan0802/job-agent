import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./api";

type State<T> = { data: T | null; loading: boolean; error: string | null };

/** Load data, exposing the three states a list has to render. */
export function useAsync<T>(load: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<State<T>>({ data: null, loading: true, error: null });

  const run = useCallback(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    load()
      .then((data) => !cancelled && setState({ data, loading: false, error: null }))
      .catch((error) => {
        if (cancelled) return;
        const message = error instanceof ApiError ? error.message : "Something went wrong";
        setState({ data: null, loading: false, error: message });
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(run, [run]);

  return { ...state, reload: run, setData: (data: T) => setState({ data, loading: false, error: null }) };
}
