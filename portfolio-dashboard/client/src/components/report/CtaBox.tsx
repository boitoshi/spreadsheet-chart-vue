/** CTA（行動喚起）ボックス — 証券口座開設の案内（ハピタス紹介リンク） */
import type React from "react";

const BROKER_LINKS = [
  {
    label: "SBI証券",
    url: "https://m.hapitas.jp/item/detail/itemid/53979?i=22359663&route=spText&apn=itemsharelink",
  },
  {
    label: "楽天証券",
    url: "https://m.hapitas.jp/item/detail/itemid/35520?i=22359663&route=spText&apn=itemsharelink",
  },
  {
    label: "マネックス証券",
    url: "https://m.hapitas.jp/item/detail/itemid/99234?i=22359663&route=spText&apn=itemsharelink",
  },
];

const HAPITAS_INVITE_URL = "https://hapitas.jp/appinvite?i=22359663&route=text";

const linkStyle: React.CSSProperties = {
  color: "#1565C0",
  fontWeight: 700,
  textDecoration: "underline",
};

export function CtaBox(): React.ReactElement {
  return (
    <div
      style={{
        background: "#eef1f7",
        borderRadius: "16px",
        padding: "20px",
      }}
    >
      {/* タイトル */}
      <p style={{ fontSize: "13px", fontWeight: 700, color: "#1e2130", margin: "0 0 8px" }}>
        📌 証券口座の開設はこちら
      </p>

      {/* 本文 */}
      <p
        style={{
          fontSize: "13px",
          color: "#3a3f52",
          lineHeight: 1.7,
          margin: "0 0 8px",
        }}
      >
        楽天証券・SBI証券・マネックス証券など、単元未満株が購入できる証券会社なら1株からポケモン関連銘柄に投資できます。口座開設はポイントサイト「
        <a href={HAPITAS_INVITE_URL} target="_blank" rel="noopener noreferrer" style={linkStyle}>
          ハピタス
        </a>
        」経由がおすすめ。口座開設だけでポイントがもらえるうえ、紹介リンクなので紹介した側・された側どちらにもポイントが入ってお互いにメリットがあります。
      </p>

      {/* 証券口座リンク（ハピタス経由） */}
      <p
        style={{
          fontSize: "13px",
          lineHeight: 1.7,
          margin: "0 0 8px",
          color: "#3a3f52",
        }}
      >
        {BROKER_LINKS.map((broker, i) => (
          <span key={broker.label}>
            {i > 0 && " / "}
            <a href={broker.url} target="_blank" rel="noopener noreferrer" style={linkStyle}>
              {broker.label}
            </a>
          </span>
        ))}
      </p>

      {/* サブテキスト */}
      <p style={{ fontSize: "12px", color: "#8c90a0", margin: 0 }}>
        みなさんもポケモン銘柄へお布施投資しましょう！
      </p>
    </div>
  );
}
