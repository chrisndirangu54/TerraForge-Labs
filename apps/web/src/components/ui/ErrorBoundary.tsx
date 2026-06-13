import { Component, type ErrorInfo, type ReactNode } from 'react';

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  error: Error | null;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('TerraForge UI error:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="mx-auto max-w-2xl rounded-xl border border-red-500/40 bg-forge-900/80 p-6">
          <h1 className="font-display text-xl text-red-300">Something went wrong</h1>
          <p className="mt-2 text-sm text-sediment-muted">
            The page failed to render. Check the browser console for details.
          </p>
          <pre className="tf-error mt-4 whitespace-pre-wrap">{this.state.error.message}</pre>
          <button
            type="button"
            className="mt-4 rounded-lg border border-forge-600 px-4 py-2 text-sm text-sediment hover:bg-forge-800"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}