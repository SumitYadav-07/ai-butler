import { useCallback, useEffect, useState } from 'react'

/** Runs an async loader on mount and whenever `deps` change. */
export function useLoad(loader, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(() => {
    setState((s) => ({ ...s, loading: true }))
    return loader()
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }))
  }, deps)

  useEffect(() => {
    run()
  }, [run])

  return { ...state, reload: run }
}