import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Deskly · Tickets de soporte",
  description: "Prototipo de sistema de tickets de soporte",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body>
        <header className="topbar">
          <span className="topbar__brand">Deskly</span>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
