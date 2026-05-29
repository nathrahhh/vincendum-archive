import type { ReactNode } from "react";

type PageSectionProps = {
  title: string;
  children: ReactNode;
};

export default function PageSection({ title, children }: PageSectionProps) {
  return (
    <section>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
