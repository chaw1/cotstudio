// Simple verification script for frontend setup
const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying frontend setup...\n');

const requiredFiles = [
  'src/App.tsx',
  'src/main.tsx',
  'src/components/layout/MainLayout.tsx',
  'src/components/layout/Header.tsx',
  'src/components/layout/Sidebar.tsx',
  'src/components/common/Loading.tsx',
  'src/components/common/ErrorBoundary.tsx',
  'src/pages/Dashboard.tsx',
  'src/stores/appStore.ts',
  'src/stores/projectStore.ts',
  'src/stores/annotationStore.ts',
  'src/services/api.ts',
  'src/services/projectService.ts',
  'src/services/annotationService.ts',
  'src/services/fileService.ts',
  'src/hooks/useApi.ts',
  'src/hooks/useProjects.ts',
  'src/hooks/useAnnotation.ts',
  'src/router/index.tsx',
  'src/types/index.ts',
  'package.json',
  'vite.config.ts',
  'tsconfig.json'
];

let allFilesExist = true;

requiredFiles.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file}`);
  } else {
    console.log(`❌ ${file} - Missing!`);
    allFilesExist = false;
  }
});

console.log('\n📦 Checking package.json dependencies...');

const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));
const requiredDeps = [
  'react',
  'react-dom',
  'antd',
  'zustand',
  'axios',
  'react-router-dom',
  '@ant-design/icons'
];

requiredDeps.forEach(dep => {
  if (packageJson.dependencies[dep]) {
    console.log(`✅ ${dep}: ${packageJson.dependencies[dep]}`);
  } else {
    console.log(`❌ ${dep} - Missing!`);
    allFilesExist = false;
  }
});

console.log('\n🎨 Checking theme and styling...');
const appCss = fs.readFileSync(path.join(__dirname, 'src/App.css'), 'utf8');
if (appCss.includes('modern-card') && appCss.includes('fade-in')) {
  console.log('✅ Modern styling classes found');
} else {
  console.log('❌ Modern styling classes missing');
  allFilesExist = false;
}

console.log('\n📱 Checking responsive design...');
if (appCss.includes('@media (max-width: 768px)')) {
  console.log('✅ Responsive design media queries found');
} else {
  console.log('❌ Responsive design media queries missing');
  allFilesExist = false;
}

console.log('\n' + '='.repeat(50));
if (allFilesExist) {
  console.log('🎉 Frontend setup verification PASSED!');
  console.log('✨ All required files and dependencies are in place');
  console.log('🚀 Ready for development');
} else {
  console.log('❌ Frontend setup verification FAILED!');
  console.log('🔧 Please check the missing files and dependencies');
}
console.log('='.repeat(50));