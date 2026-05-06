import Link from "next/link";

export default function HomePage() {
  return (
    <main
      style={{
        fontFamily: "system-ui",
        padding: "4rem 1.5rem",
        maxWidth: 720,
        margin: "0 auto",
      }}
    >
      <h1 style={{ fontSize: "2rem", marginBottom: "1rem" }}>Voice-Pro</h1>
      <p style={{ color: "#444", lineHeight: 1.6 }}>
        Landing scaffold (Epic 1). Analytics: set{" "}
        <code>NEXT_PUBLIC_PLAUSIBLE_DOMAIN</code> để bật Plausible.
      </p>
      <p style={{ marginTop: "2rem" }}>
        <Link href="https://github.com">GitHub</Link>
      </p>
    </main>
  );
}
