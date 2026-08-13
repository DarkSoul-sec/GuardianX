import ErrorBoundary from "@/shared/components/ErrorBoundary";
import AppRouter from "./routes/AppRouter";

export default function App() {
  return (
    <ErrorBoundary>
      <AppRouter />
    </ErrorBoundary>
  );
}
