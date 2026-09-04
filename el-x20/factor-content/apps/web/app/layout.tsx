import Link from "next/link";
import { ReactNode } from "react";

export const metadata = { title: "Factor Content" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body style={{ margin: 0 }}>
        <nav style={{ display: "flex", gap: 16, padding: 16, borderBottom: "1px solid #ddd", fontFamily: "system-ui" }}>
          <Link href="/dashboard">Inicio</Link>
          <Link href="/queue">Importar</Link>
          <Link href="/review">Revisión</Link>
          <Link href="/templates">Plantillas</Link>
          <Link href="/accounts">Cuentas</Link>
          <Link href="/calendar">Calendario</Link>
          <Link href="/analytics">Métricas</Link>
          <Link href="/login">Acceso</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
