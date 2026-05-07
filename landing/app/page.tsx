import Link from "next/link";

const features = [
  {
    icon: "🎙️",
    title: "Dub bất kỳ video",
    desc: "Nghe bất kỳ video YouTube nào bằng giọng nói tiếng Việt hoặc 30+ ngôn ngữ khác theo thời gian thực.",
  },
  {
    icon: "⚡",
    title: "Latency cực thấp",
    desc: "Pipeline streaming Whisper → MT → TTS. Âm thanh dub bắt đầu phát trước 3 giây sau khi video chạy.",
  },
  {
    icon: "🔒",
    title: "Bảo mật & Riêng tư",
    desc: "Xử lý toàn bộ trên server. Không lưu audio sau khi dub xong. Token OAuth không bao giờ rời thiết bị của bạn.",
  },
  {
    icon: "💳",
    title: "Miễn phí để thử",
    desc: "30 phút credit mỗi tháng không cần thẻ. Nâng cấp Pro khi bạn cần không giới hạn.",
  },
];

export default function HomePage() {
  return (
    <>
      {/* Nav */}
      <nav
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 40px",
          borderBottom: "1px solid rgba(14,15,12,0.08)",
          position: "sticky",
          top: 0,
          background: "rgba(255,255,255,0.95)",
          backdropFilter: "blur(8px)",
          zIndex: 100,
          fontFamily: "'Inter',Helvetica,Arial,sans-serif",
        }}
      >
        <span
          style={{
            fontSize: 20,
            fontWeight: 900,
            letterSpacing: "-0.5px",
            color: "#0e0f0c",
            fontFeatureSettings: '"calt"',
          }}
        >
          Voice<span style={{ color: "#9fe870" }}>Pro</span>
        </span>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Link href="https://github.com" className="nav-link">
            GitHub
          </Link>
          <a
            href="#pricing"
            className="btn-primary"
            style={{ fontSize: 15, padding: "8px 20px" }}
          >
            Dùng miễn phí
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section
        style={{
          padding: "96px 40px 80px",
          maxWidth: 1120,
          margin: "0 auto",
          textAlign: "center",
          fontFamily: "'Inter',Helvetica,Arial,sans-serif",
        }}
      >
        <div
          style={{
            display: "inline-block",
            background: "#e2f6d5",
            color: "#163300",
            fontSize: 13,
            fontWeight: 600,
            padding: "6px 16px",
            borderRadius: 9999,
            marginBottom: 32,
            letterSpacing: "0.02em",
          }}
        >
          ✦ Chrome Extension • Miễn phí 30 phút/tháng
        </div>
        <h1
          style={{
            fontSize: "clamp(56px, 8vw, 96px)",
            fontWeight: 900,
            lineHeight: 0.85,
            letterSpacing: "-2px",
            color: "#0e0f0c",
            margin: "0 0 32px",
            fontFeatureSettings: '"calt"',
          }}
        >
          Dub mọi video
          <br />
          <span style={{ color: "#9fe870" }}>ngay trình duyệt</span>
        </h1>
        <p
          style={{
            fontSize: 20,
            fontWeight: 400,
            lineHeight: 1.55,
            color: "#454745",
            maxWidth: 560,
            margin: "0 auto 48px",
          }}
        >
          Voice-Pro tự động lồng tiếng bất kỳ video YouTube nào sang tiếng Việt và 30+ ngôn ngữ khác — ngay khi bạn xem.
        </p>
        <div style={{ display: "flex", gap: 16, justifyContent: "center", flexWrap: "wrap" }}>
          <a
            href="https://chrome.google.com/webstore"
            className="btn-primary"
            style={{ fontSize: 18 }}
          >
            Cài ngay — Miễn phí
          </a>
          <a
            href="#features"
            className="btn-secondary"
          >
            Xem tính năng ↓
          </a>
        </div>

        {/* Social proof */}
        <p style={{ marginTop: 40, fontSize: 14, color: "#868685", fontWeight: 400 }}>
          Không cần thẻ tín dụng · Hoạt động ngay sau cài đặt · 30 phút/tháng miễn phí
        </p>
      </section>

      {/* Demo preview */}
      <section
        style={{
          padding: "0 40px 80px",
          maxWidth: 960,
          margin: "0 auto",
        }}
      >
        <div
          style={{
            background: "#0e0f0c",
            borderRadius: 40,
            aspectRatio: "16/9",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "rgba(14,15,12,0.2) 0px 32px 80px -16px",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "radial-gradient(ellipse at 60% 40%, rgba(159,232,112,0.15) 0%, transparent 60%)",
            }}
          />
          <div style={{ textAlign: "center", zIndex: 1 }}>
            <div style={{ fontSize: 64, marginBottom: 16 }}>🎬</div>
            <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 16, fontWeight: 600, fontFamily: "'Inter',sans-serif" }}>
              Extension Popup Preview
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section
        id="features"
        style={{
          padding: "80px 40px",
          background: "#f8faf7",
          fontFamily: "'Inter',Helvetica,Arial,sans-serif",
        }}
      >
        <div style={{ maxWidth: 1120, margin: "0 auto" }}>
          <h2
            style={{
              fontSize: "clamp(40px, 5vw, 64px)",
              fontWeight: 900,
              lineHeight: 0.85,
              color: "#0e0f0c",
              marginBottom: 16,
              fontFeatureSettings: '"calt"',
            }}
          >
            Tại sao Voice-Pro?
          </h2>
          <p
            style={{
              fontSize: 18,
              color: "#454745",
              marginBottom: 56,
              fontWeight: 400,
              maxWidth: 480,
              lineHeight: 1.55,
            }}
          >
            Được xây dựng cho tốc độ và độ tự nhiên — không phải bản dịch robot.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: 24,
            }}
          >
            {features.map((f) => (
              <div key={f.title} className="feature-card">
                <div style={{ fontSize: 36, marginBottom: 16 }}>{f.icon}</div>
                <h3
                  style={{
                    fontSize: 22,
                    fontWeight: 600,
                    margin: "0 0 10px",
                    letterSpacing: "-0.396px",
                    lineHeight: 1.25,
                  }}
                >
                  {f.title}
                </h3>
                <p style={{ fontSize: 16, color: "#454745", margin: 0, lineHeight: 1.55, fontWeight: 400 }}>
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section
        id="pricing"
        style={{
          padding: "96px 40px",
          maxWidth: 1120,
          margin: "0 auto",
          fontFamily: "'Inter',Helvetica,Arial,sans-serif",
        }}
      >
        <h2
          style={{
            fontSize: "clamp(40px, 5vw, 64px)",
            fontWeight: 900,
            lineHeight: 0.85,
            textAlign: "center",
            marginBottom: 16,
            fontFeatureSettings: '"calt"',
          }}
        >
          Đơn giản, minh bạch
        </h2>
        <p
          style={{
            textAlign: "center",
            color: "#454745",
            fontSize: 18,
            fontWeight: 400,
            marginBottom: 56,
          }}
        >
          Không phí ẩn. Nâng cấp hoặc hủy bất cứ lúc nào.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: 24,
            maxWidth: 720,
            margin: "0 auto",
          }}
        >
          {/* Free */}
          <div
            style={{
              borderRadius: 30,
              padding: "40px 32px",
              boxShadow: "rgba(14,15,12,0.12) 0px 0px 0px 1px",
            }}
          >
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: "#454745",
                marginBottom: 16,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              Free
            </div>
            <div style={{ fontSize: 48, fontWeight: 900, marginBottom: 8, lineHeight: 1 }}>
              $0
            </div>
            <p style={{ color: "#454745", fontSize: 15, fontWeight: 400, marginBottom: 32, lineHeight: 1.55 }}>
              Mỗi tháng · Tự động reset
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 32px", display: "flex", flexDirection: "column", gap: 10 }}>
              {["30 phút/tháng", "Tất cả ngôn ngữ", "Cài đặt Chrome"].map((item) => (
                <li key={item} style={{ fontSize: 15, color: "#0e0f0c", fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: "#054d28", fontWeight: 700 }}>✓</span> {item}
                </li>
              ))}
            </ul>
            <a href="https://chrome.google.com/webstore" className="btn-secondary" style={{ width: "100%", justifyContent: "center" }}>
              Bắt đầu
            </a>
          </div>

          {/* Pro */}
          <div
            style={{
              borderRadius: 30,
              padding: "40px 32px",
              background: "#0e0f0c",
              color: "#ffffff",
              position: "relative",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: 0,
                right: 0,
                width: 200,
                height: 200,
                background: "radial-gradient(circle, rgba(159,232,112,0.2) 0%, transparent 70%)",
              }}
            />
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: "#9fe870",
                marginBottom: 16,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              Pro
            </div>
            <div style={{ fontSize: 48, fontWeight: 900, marginBottom: 8, lineHeight: 1 }}>
              $9<span style={{ fontSize: 20, fontWeight: 400, opacity: 0.7 }}>/tháng</span>
            </div>
            <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 15, fontWeight: 400, marginBottom: 32, lineHeight: 1.55 }}>
              Không giới hạn · Ưu tiên xử lý
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 32px", display: "flex", flexDirection: "column", gap: 10 }}>
              {["Không giới hạn phút", "Tất cả ngôn ngữ", "Xử lý ưu tiên", "Hỗ trợ email"].map((item) => (
                <li key={item} style={{ fontSize: 15, fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: "#9fe870", fontWeight: 700 }}>✓</span> {item}
                </li>
              ))}
            </ul>
            <a href="https://chrome.google.com/webstore" className="btn-primary" style={{ width: "100%", justifyContent: "center" }}>
              Nâng cấp Pro
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer
        style={{
          borderTop: "1px solid rgba(14,15,12,0.08)",
          padding: "40px",
          textAlign: "center",
          fontFamily: "'Inter',Helvetica,Arial,sans-serif",
        }}
      >
        <p style={{ color: "#868685", fontSize: 14, fontWeight: 400, margin: 0 }}>
          © 2026 VoicePro · <Link href="https://github.com" style={{ color: "#454745", textDecoration: "underline" }}>GitHub</Link>
        </p>
      </footer>
    </>
  );
}
