import {themes as prismThemes} from 'prism-react-renderer';

const pagesUrl = process.env.CI_PAGES_URL ? new URL(process.env.CI_PAGES_URL) : null;
const siteUrl = process.env.DOCUSAURUS_URL || pagesUrl?.origin || 'https://pthink21.github.io';
const baseUrl = process.env.DOCUSAURUS_BASE_URL || (pagesUrl
  ? `${pagesUrl.pathname.replace(/\/$/, '')}/`
  : '/THLTANTT_2387700066_NPT/');

const config = {
  title: 'DevSecOps Lab',
  tagline: 'Tích hợp bảo mật xuyên suốt CI/CD',
  favicon: 'img/favicon.svg',
  url: siteUrl,
  baseUrl,
  organizationName: 'pthink21',
  projectName: 'THLTANTT_2387700066_NPT',
  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },
  i18n: {
    defaultLocale: 'vi',
    locales: ['vi'],
  },
  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          sidebarPath: './sidebars.js',
          editUrl: 'https://github.com/pthink21/THLTANTT_2387700066_NPT/tree/main/Buoi6/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      },
    ],
  ],
  themeConfig: {
    image: 'img/devsecops-social-card.svg',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'DEVSECOPS / 06',
      logo: {
        alt: 'DevSecOps mark',
        src: 'img/mark.svg',
      },
      items: [
        {type: 'docSidebar', sidebarId: 'labSidebar', position: 'left', label: 'Nội dung'},
        {href: 'https://github.com/pthink21/THLTANTT_2387700066_NPT', label: 'GitHub', position: 'right'},
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Bài thực hành',
          items: [
            {label: 'Pipeline an toàn', to: '/secure-pipeline'},
            {label: 'Thực hành GitLab CI/CD', to: '/gitlab-cicd'},
            {label: 'Kết quả & minh chứng', to: '/results'},
          ],
        },
        {
          title: 'Sinh viên',
          items: [
            {label: 'Nguyễn Phúc Thịnh · 2387700066', href: 'https://github.com/pthink21'},
          ],
        },
      ],
      copyright: '© 2026 Nguyễn Phúc Thịnh · Lập trình An toàn Thông tin',
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  },
};

export default config;
