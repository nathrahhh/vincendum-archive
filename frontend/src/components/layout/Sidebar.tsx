import { NavLink } from "react-router-dom";
import { useCurrentUser } from "../../auth/CurrentUserProvider";

const allLinks = [
  { to: "/dashboard", label: "Dashboard", roles: ["admin"] as const },
  { to: "/client", label: "My Client", roles: ["client"] as const },
  { to: "/deal", label: "Deal", roles: ["client"] as const },
  { to: "/apply", label: "Apply", roles: ["client"] as const },
  { to: "/client-financials", label: "Client Financials", roles: ["client"] as const },
  { to: "/evaluations", label: "Evaluations", roles: ["admin"] as const },
  { to: "/breaches", label: "Breaches", roles: ["admin"] as const },
  { to: "/clients", label: "Clients", roles: ["admin"] as const },
  { to: "/client-applications", label: "Client Applications", roles: ["admin"] as const },
] as const;

export default function Sidebar() {
  const { role } = useCurrentUser();
  const links = allLinks.filter((link) =>
    (link.roles as readonly string[]).includes(role),
  );

  return (
    <aside className="app-sidebar">
      <div className="app-sidebar__brand">Credit Risk Engine</div>
      <nav className="app-sidebar__nav">
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              isActive
                ? "app-sidebar__link app-sidebar__link--active"
                : "app-sidebar__link"
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
