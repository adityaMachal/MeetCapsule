import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MeetCapsule AI | Meeting Intelligence",
  description: "Transform video into structured intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
