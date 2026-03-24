export interface QualityCheck {
  name: string;
  passed: boolean;
  details?: string;
}

interface QualityScoreCardProps {
  score: number;
  checks: QualityCheck[];
  overallStatus?: "pass" | "fail";
}

function scoreColor(score: number): string {
  if (score >= 90) return "#22c55e";
  if (score >= 70) return "#eab308";
  return "#ef4444";
}

function statusBanner(status: "pass" | "fail"): string {
  return status === "pass"
    ? "bg-green-50 border-green-200 text-green-800"
    : "bg-red-50 border-red-200 text-red-800";
}

function ScoreGauge({ score }: { score: number }): React.JSX.Element {
  const radius = 54;
  const stroke = 10;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, score));
  const dashOffset = circumference - (clampedScore / 100) * circumference;
  const color = scoreColor(score);

  return (
    <div className="relative mx-auto h-36 w-36">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 128 128">
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={stroke}
        />
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold" style={{ color }}>
          {clampedScore}
        </span>
        <span className="text-xs text-gray-500">/ 100</span>
      </div>
    </div>
  );
}

export default function QualityScoreCard({
  score,
  checks,
  overallStatus,
}: QualityScoreCardProps): React.JSX.Element {
  const status = overallStatus ?? (score >= 70 ? "pass" : "fail");
  const passed = checks.filter((c) => c.passed).length;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5">
      {/* Status banner */}
      <div
        className={`mb-4 rounded-md border px-3 py-2 text-center text-sm font-medium ${statusBanner(status)}`}
      >
        {status === "pass" ? "✓ Quality Gate Passed" : "✗ Quality Gate Failed"}
      </div>

      {/* Gauge */}
      <ScoreGauge score={score} />

      {/* Summary */}
      <p className="mt-3 text-center text-xs text-gray-500">
        {passed}/{checks.length} checks passed
      </p>

      {/* Check list */}
      {checks.length > 0 && (
        <ul className="mt-4 space-y-2">
          {checks.map((check) => (
            <li key={check.name} className="flex items-start gap-2 text-sm">
              <span
                className={`mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold text-white ${
                  check.passed ? "bg-green-500" : "bg-red-500"
                }`}
              >
                {check.passed ? "✓" : "✗"}
              </span>
              <div className="min-w-0">
                <span className="font-medium text-gray-700">{check.name}</span>
                {check.details && (
                  <p className="mt-0.5 text-xs text-gray-400">{check.details}</p>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
