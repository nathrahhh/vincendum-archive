import { DevRoleProvider } from "./devRole";
import { AppRouter } from "./router";

export default function App() {
  return (
    <DevRoleProvider>
      <AppRouter />
    </DevRoleProvider>
  );
}
