import { Component, type ErrorInfo, type ReactNode } from "react";

import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error("ErrorBoundary caught:", error, info);
  }

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children;

    if (this.props.fallback) return this.props.fallback;

    return (
      <div className="flex flex-col items-center justify-center gap-4 py-32 text-center">
        <AlertTriangle size={48} className="text-red-500" />
        <h2 className="text-2xl font-bold text-white">
          Something went wrong
        </h2>
        <p className="max-w-md text-slate-400">
          An unexpected error occurred while rendering this view.
        </p>
        <button
          onClick={() => this.setState({ hasError: false })}
          className="rounded-xl bg-cyan-600 px-5 py-2 font-semibold text-white transition hover:bg-cyan-500"
        >
          Try again
        </button>
      </div>
    );
  }
}
