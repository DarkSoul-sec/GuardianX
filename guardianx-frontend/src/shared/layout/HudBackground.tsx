import { cn } from "@/shared/utils/cn";

interface Props {
  className?: string;
}

/**
 * Full-screen sci-fi backdrop: neon grid, ambient glows and a drifting
 * scanline. Rendered behind the app shell (fixed, pointer-events none).
 */
export default function HudBackground({ className }: Props) {
  return (
    <div
      aria-hidden="true"
      className={cn("pointer-events-none fixed inset-0 z-0 overflow-hidden", className)}
    >
      <div className="absolute inset-0 bg-canvas" />

      {/* Neon grid, faded toward the edges. */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,207,255,0.055) 1px, transparent 1px), linear-gradient(90deg, rgba(0,207,255,0.055) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage:
            "radial-gradient(ellipse 120% 90% at 50% 0%, #000 30%, transparent 75%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 120% 90% at 50% 0%, #000 30%, transparent 75%)",
        }}
      />

      {/* Ambient neon glows. */}
      <div className="absolute inset-0">
        <div className="absolute left-1/2 top-[-10%] h-[46rem] w-[60rem] -translate-x-1/2 rounded-full bg-cyan-500/15 blur-[140px]" />
        <div className="absolute bottom-[-15%] right-[-5%] h-[36rem] w-[36rem] rounded-full bg-violet-600/10 blur-[140px]" />
        <div className="absolute left-[-8%] top-[35%] h-[30rem] w-[30rem] rounded-full bg-blue-600/10 blur-[130px]" />
      </div>

      {/* Drifting scanline. */}
      <div className="absolute left-0 top-0 h-px w-full bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent animate-[scanline_9s_linear_infinite]" />
    </div>
  );
}
