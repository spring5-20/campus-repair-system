/**
 * 运行时冒烟测试（jsdom）
 * - 验证登录页可正常渲染
 * - 模拟已登录状态后验证工作台页可正常渲染
 * 运行：npm run smoke
 */

import { JSDOM } from 'jsdom';

const dom = new JSDOM(
  '<!doctype html><html><body><div id="root"></div></body></html>',
  {
    url: 'http://localhost:5173/#/login',
    pretendToBeVisual: true,
    runScripts: 'outside-only',
  },
);

const { window } = dom;

for (const key of [
  'window',
  'document',
  'location',
  'history',
  'localStorage',
  'sessionStorage',
  'HTMLElement',
  'Element',
  'Node',
  'SVGElement',
  'DocumentFragment',
  'Text',
  'Comment',
  'Document',
  'Event',
  'CustomEvent',
  'MouseEvent',
  'KeyboardEvent',
  'InputEvent',
  'FocusEvent',
  'PointerEvent',
  'MutationObserver',
  'getComputedStyle',
]) {
  global[key] = window[key];
}

Object.defineProperty(global, 'navigator', {
  value: window.navigator,
  configurable: true,
});

window.requestAnimationFrame = (callback) => setTimeout(callback, 16);
global.requestAnimationFrame = window.requestAnimationFrame;
window.cancelAnimationFrame = (id) => clearTimeout(id);
global.cancelAnimationFrame = window.cancelAnimationFrame;

window.matchMedia =
  window.matchMedia ||
  ((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener() {},
    removeListener() {},
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent() {
      return false;
    },
  }));
global.matchMedia = window.matchMedia;

class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver = ResizeObserver;
global.ResizeObserver = ResizeObserver;

class ShadowRoot {}
window.ShadowRoot = ShadowRoot;
global.ShadowRoot = ShadowRoot;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const React = (await import('react')).default;
const { createRoot } = await import('react-dom/client');
const { ConfigProvider, App: AntApp } = await import('antd');
const zhCN = (await import('antd/locale/zh_CN.js')).default;
const { default: App } = await import('../src/App.jsx');

const root = createRoot(document.getElementById('root'));
root.render(
  React.createElement(
    React.StrictMode,
    null,
    React.createElement(
      ConfigProvider,
      { locale: zhCN },
      React.createElement(AntApp, null, React.createElement(App)),
    ),
  ),
);

let failed = false;
const check = (name, ok) => {
  console.log(`${ok ? '✅' : '❌'} ${name}`);
  if (!ok) failed = true;
};
const phase = (name) => console.log(`—— 阶段：${name} ——`);

process.on('uncaughtException', (error) => {
  console.error('未捕获异常:', error?.message);
  console.error(error?.stack);
  process.exit(1);
});

phase('登录页');
await sleep(800);
const loginHtml = document.body.innerHTML;
check('登录页渲染「校园报修协同系统」', loginHtml.includes('校园报修协同系统'));
check('登录页渲染「登录系统」按钮', loginHtml.includes('登录系统'));

phase('鉴权跳转');
localStorage.setItem(
  'reac-admin-auth',
  JSON.stringify({ id: 1, username: 'student', fullName: '学生用户', role: 'student' }),
);
window.location.hash = '#/student/workbench';
await sleep(1200);

  const workbenchHtml = document.body.innerHTML;
  check('工作台页渲染「维修工作台」', workbenchHtml.includes('维修工作台'));
  check('工作台页渲染「最近工单」', workbenchHtml.includes('最近工单'));
  check('学生菜单不包含运维端入口', !workbenchHtml.includes('工作池'));
  check('学生菜单不包含管理端入口', !workbenchHtml.includes('数据看板'));

phase('越权访问拦截');
window.location.hash = '#/admin/dashboard';
await sleep(800);

const forbiddenHtml = document.body.innerHTML;
check('学生访问管理端被重定向回工作台', forbiddenHtml.includes('维修工作台'));
check('学生无法看到管理端页面', !forbiddenHtml.includes('数据看板'));

phase('稳定性检查');
await sleep(800);
root.unmount();

if (failed) {
  console.error('\n冒烟测试存在失败项');
  process.exit(1);
}

console.log('\n冒烟测试全部通过');
process.exit(0);
