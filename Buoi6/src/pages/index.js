import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import styles from './index.module.css';

const pillars = [
  {number: '01', title: 'Bảo vệ mã nguồn', text: 'SAST, secret scanning và dependency audit chạy trước khi build.'},
  {number: '02', title: 'Build có kiểm soát', text: 'Unit test và artifact nối tiếp nhau theo thứ tự stage rõ ràng.'},
  {number: '03', title: 'Triển khai có điều kiện', text: 'Chỉ nhánh mặc định được xuất bản sau khi các security gate đạt.'},
];

export default function Home() {
  return (
    <Layout title="DevSecOps Lab" description="Bài thực hành DevSecOps của Nguyễn Phúc Thịnh">
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroCopy}>
            <div className={styles.eyebrow}><span /> LAB 06 · SECURE DELIVERY</div>
            <h1>Bảo mật chạy<br/><em>cùng</em> pipeline.</h1>
            <p className={styles.lede}>Tích hợp kiểm thử bảo mật vào từng bước CI/CD — từ commit đầu tiên đến artifact sẵn sàng triển khai.</p>
            <div className={styles.actions}>
              <Link className={styles.primary} to="/secure-pipeline">Khám phá bài thực hành <span>↗</span></Link>
              <Link className={styles.secondary} to="/gitlab-cicd">Xem pipeline GitLab</Link>
            </div>
            <div className={styles.identity}><span>THỰC HIỆN BỞI</span><strong>Nguyễn Phúc Thịnh</strong><span className={styles.dot}>·</span><strong>2387700066</strong></div>
          </div>
          <div className={styles.visual} aria-label="Sơ đồ các lớp bảo mật trong pipeline">
            <div className={`${styles.orbit} ${styles.orbitOne}`} /><div className={`${styles.orbit} ${styles.orbitTwo}`} />
            <div className={styles.core}><span>SECURE</span><strong>CI/CD</strong><small>EVERY COMMIT</small></div>
            <div className={`${styles.node} ${styles.nodeTop}`}><b>01</b><span>CODE</span></div>
            <div className={`${styles.node} ${styles.nodeRight}`}><b>02</b><span>TEST</span></div>
            <div className={`${styles.node} ${styles.nodeBottom}`}><b>03</b><span>SCAN</span></div>
            <div className={`${styles.node} ${styles.nodeLeft}`}><b>04</b><span>SHIP</span></div>
            <div className={styles.signal}>GATES ACTIVE <i>●</i></div>
          </div>
          <div className={styles.heroIndex}>DEVSECOPS<br/>FIELD NOTES <span>06 / 06</span></div>
        </section>
        <section className={styles.section}>
          <div className={styles.sectionHead}><div><span className={styles.kicker}>SECURITY BY DESIGN</span><h2>Kiểm tra sớm.<br/>Phát hành tự tin.</h2></div><p>Pipeline biến yêu cầu bảo mật thành các bước kiểm tra lặp lại được. Mỗi gate có nhiệm vụ cụ thể và chặn luồng khi phát hiện vấn đề nghiêm trọng.</p></div>
          <div className={styles.pillars}>{pillars.map((item) => <article className={styles.card} key={item.number}><span>{item.number}</span><h3>{item.title}</h3><p>{item.text}</p><div className={styles.cardLine} /></article>)}</div>
        </section>
        <section className={styles.callout}><span>LAB / 06</span><div><h2>Từ lý thuyết đến pipeline thật.</h2><p>Đọc hướng dẫn, xem cấu hình YAML và chạy lại các bước trên project của bạn.</p></div><Link to="/gitlab-cicd">Bắt đầu <b>→</b></Link></section>
      </main>
    </Layout>
  );
}
