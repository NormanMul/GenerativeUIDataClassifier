import { useState, useEffect } from "react";

const ROLES = ["Business Analyst", "Data Engineer", "Data Steward"] as const;
export type Role = (typeof ROLES)[number];

const STORAGE_KEY = "udc-selected-role";

const ROLE_ICONS: Record<Role, string> = {
  "Business Analyst": "📊",
  "Data Engineer": "⚙️",
  "Data Steward": "🛡️",
};

export function getStoredRole(): Role {
  const stored = localStorage.getItem(STORAGE_KEY);
  return ROLES.includes(stored as Role) ? (stored as Role) : ROLES[0];
}

export default function RoleSelector(): React.JSX.Element {
  const [role, setRole] = useState<Role>(getStoredRole);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, role);
  }, [role]);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-md border border-blue-400/30 bg-white/10 px-3 py-1.5 text-sm text-white transition-colors hover:bg-white/20"
      >
        <span>{ROLE_ICONS[role]}</span>
        <span>{role}</span>
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-1 w-52 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg">
            {ROLES.map((r) => (
              <button
                key={r}
                onClick={() => {
                  setRole(r);
                  setOpen(false);
                }}
                className={`flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm transition-colors hover:bg-gray-50 ${
                  r === role ? "bg-blue-50 font-medium text-blue-700" : "text-gray-700"
                }`}
              >
                <span>{ROLE_ICONS[r]}</span>
                <span>{r}</span>
                {r === role && (
                  <svg className="ml-auto h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
