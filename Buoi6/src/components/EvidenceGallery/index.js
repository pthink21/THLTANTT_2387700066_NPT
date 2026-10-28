import React from 'react';
import useBaseUrl from '@docusaurus/useBaseUrl';
import styles from './styles.module.css';

const captions = [
  'Node.js runtime', 'npm package manager', 'Git client', 'Project package metadata',
  'First GitLab CI job', 'Four-job pipeline example', 'Pipeline structure tests', 'Documentation tests',
  'Complete test suite', 'Security policy gate', 'Pipeline YAML syntax', 'Dependency audit',
  'Production static build', 'Generated build files', 'Build SHA-256 manifest', 'Local preview HTTP response',
  'Artifact manifest contents', 'Default branch deployment rule', 'Responsive layout breakpoints', 'Git whitespace and status check',
];

export default function EvidenceGallery() {
  const evidenceBase = useBaseUrl('/evidence/');
  return (
    <div className={styles.grid}>
      {captions.map((caption, index) => {
        const id = String(index + 1).padStart(2, '0');
        const src = `${evidenceBase}${id}-cmd.png`;
        return (
          <figure className={styles.item} key={id}>
            <a href={src} target="_blank" rel="noreferrer">
              <img src={src} alt={`Ảnh ${id}: ${caption}, chụp từ CMD`} loading="lazy" />
            </a>
            <figcaption><span>{id}</span>{caption}</figcaption>
          </figure>
        );
      })}
    </div>
  );
}
