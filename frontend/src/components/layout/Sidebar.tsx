import { NavLink } from "react-router-dom";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/deal", label: "Deal" },
  { to: "/evaluations", label: "Evaluations" },
  { to: "/breaches", label: "Breaches" },
] as const;

export default function Sidebar() {
  return (
    <aside className="app-sidebar">
      <div className="app-sidebar__brand">Credit Risk Engine</div>
      <nav className="app-sidebar__nav">
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              isActive ? "app-sidebar__link app-sidebar__link--active" : "app-sidebar__link"
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
