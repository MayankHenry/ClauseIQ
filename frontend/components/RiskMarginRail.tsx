import type { RiskFlagItem } from "@/lib/api";
import { severityBand, SEVERITY_STYLES } from "@/lib/severity";

interface RiskMarginRailProps {
  flags: RiskFlagItem[];
  activeIndex: number | null;
  onSelect: (index: number) => void;
}

/**
 * The signature element of the risk-review view: a vertical margin rail
 * with one tick per flagged clause, colored by severity -- echoing how a
 * lawyer marks up a paper contract in the margin rather than a generic
 * dashboard widget. Ticks are only drawn for clauses that actually need
 * attention (same as a real margin: nobody annotates the boilerplate
 * that's fine).
 */
export default function RiskMarginRail({ flags, activeIndex, onSelect }: RiskMarginRailProps) {
  if (flags.length === 0) return null;

  return (
    <div className="relative hidden w-10 flex-shrink-0 sm:block">
      <div className="absolute bottom-0 top-0 left-4 w-px bg-rule" />
      <ol className="relative flex flex-col gap-0">
        {flags.map((flag, i) => {
          const band = severityBand(flag.severity);
          const style = SEVERITY_STYLES[band];
          const isActive = activeIndex === i;
          return (
            <li key={i} style={{ marginTop: i === 0 ? 0 : "1.75rem" }}>
              <button
                aria-label={`Jump to flag ${i + 1}: ${style.label}`}
                onClick={() => onSelect(i)}
                className="group relative flex h-6 w-8 items-center"
              >
                <span
                  className={`relative z-10 h-2.5 w-2.5 rounded-full border-2 border-paper transition-transform ${style.dot} ${
                    isActive ? "scale-125" : "group-hover:scale-110"
                  }`}
                />
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
