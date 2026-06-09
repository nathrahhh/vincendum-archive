import { defaultPathForRole, useDevRole } from "../../devRole";
import type { DevRole } from "../../devRole";
import { useNavigate } from "react-router-dom";

const options: { value: DevRole; label: string }[] = [
  { value: "client", label: "Client" },
  { value: "admin", label: "Admin" },
];

export default function RoleSwitcher() {
  const { role, setRole } = useDevRole();
  const navigate = useNavigate();

  function handleChange(next: DevRole) {
    setRole(next);
    navigate(defaultPathForRole(next), { replace: true });
  }

  return (
    <div className="role-switcher">
      <p className="role-switcher__label">Dev role</p>
      <div className="role-switcher__buttons">
        {options.map(({ value, label }) => (
          <button
            key={value}
            type="button"
            className={role === value ? "role-switcher__btn role-switcher__btn--active" : "role-switcher__btn"}
            onClick={() => handleChange(value)}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
