/**
 * Test Runner for Comprehensive Responsive Behavior Testing
 * 
 * This script runs all responsive behavior tests and generates a report
 * 
 * Requirements: 1.4, 2.4, 3.4
 */

import { execSync } from 'child_process';
import { writeFileSync } from 'fs';
import { join } from 'path';

interface TestResult {
  testFile: string;
  passed: boolean;
  duration: number;
  errors: string[];
  coverage?: {
    statements: number;
    branches: number;
    functions: number;
    lines: number;
  };
}

interface TestReport {
  timestamp: string;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  totalDuration: number;
  results: TestResult[];
  summary: {
    layoutBehavior: boolean;
    sidebarFunctionality: boolean;
    modalPositioning: boolean;
    touchInteractions: boolean;
    viewportAdaptation: boolean;
  };
}

const RESPONSIVE_TEST_FILES = [
  'responsive-behavior.test.tsx',
  'touch-interactions.test.tsx',
  'viewport-breakpoints.test.tsx',
  'modal-positioning.test.tsx',
  'modal-footer.test.tsx'
];

/**
 * Run a single test file and capture results
 */
async function runTestFile(testFile: string): Promise<TestResult> {
  const startTime = Date.now();
  
  try {
    console.log(`🧪 Running ${testFile}...`);
    
    const output = execSync(
      `npm run test:run -- --reporter=json src/test/${testFile}`,
      { 
        encoding: 'utf8',
        cwd: process.cwd(),
        timeout: 30000 // 30 second timeout per test file
      }
    );
    
    const duration = Date.now() - startTime;
    
    // Parse test output (simplified - in real implementation would parse JSON reporter output)
    const passed = !output.includes('FAILED') && !output.includes('Error');
    
    return {
      testFile,
      passed,
      duration,
      errors: passed ? [] : ['Test execution failed']
    };
    
  } catch (error) {
    const duration = Date.now() - startTime;
    
    return {
      testFile,
      passed: false,
      duration,
      errors: [error instanceof Error ? error.message : String(error)]
    };
  }
}

/**
 * Run all responsive behavior tests
 */
async function runAllResponsiveTests(): Promise<TestReport> {
  console.log('🚀 Starting Comprehensive Responsive Behavior Testing...\n');
  
  const startTime = Date.now();
  const results: TestResult[] = [];
  
  // Run each test file
  for (const testFile of RESPONSIVE_TEST_FILES) {
    const result = await runTestFile(testFile);
    results.push(result);
    
    if (result.passed) {
      console.log(`✅ ${testFile} - PASSED (${result.duration}ms)`);
    } else {
      console.log(`❌ ${testFile} - FAILED (${result.duration}ms)`);
      result.errors.forEach(error => console.log(`   Error: ${error}`));
    }
  }
  
  const totalDuration = Date.now() - startTime;
  const passedTests = results.filter(r => r.passed).length;
  const failedTests = results.length - passedTests;
  
  // Generate summary based on test results
  const summary = {
    layoutBehavior: results.find(r => r.testFile.includes('responsive-behavior'))?.passed || false,
    sidebarFunctionality: results.find(r => r.testFile.includes('responsive-behavior'))?.passed || false,
    modalPositioning: results.find(r => r.testFile.includes('modal-positioning'))?.passed || false,
    touchInteractions: results.find(r => r.testFile.includes('touch-interactions'))?.passed || false,
    viewportAdaptation: results.find(r => r.testFile.includes('viewport-breakpoints'))?.passed || false
  };
  
  const report: TestReport = {
    timestamp: new Date().toISOString(),
    totalTests: results.length,
    passedTests,
    failedTests,
    totalDuration,
    results,
    summary
  };
  
  return report;
}

/**
 * Generate HTML test report
 */
function generateHtmlReport(report: TestReport): string {
  const { summary } = report;
  const overallStatus = report.failedTests === 0 ? 'PASSED' : 'FAILED';
  const statusColor = overallStatus === 'PASSED' ? '#52c41a' : '#ff4d4f';
  
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Responsive Behavior Test Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: ${statusColor};
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .status {
            font-size: 18px;
            font-weight: bold;
            margin-top: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 20px;
            background: #fafafa;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #1890ff;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .requirements {
            padding: 20px;
        }
        .requirement {
            display: flex;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            background: #f9f9f9;
        }
        .requirement.passed {
            background: #f6ffed;
            border-left: 4px solid #52c41a;
        }
        .requirement.failed {
            background: #fff2f0;
            border-left: 4px solid #ff4d4f;
        }
        .requirement-icon {
            margin-right: 10px;
            font-size: 18px;
        }
        .test-results {
            padding: 20px;
        }
        .test-result {
            margin: 10px 0;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #d9d9d9;
        }
        .test-result.passed {
            background: #f6ffed;
            border-color: #b7eb8f;
        }
        .test-result.failed {
            background: #fff2f0;
            border-color: #ffccc7;
        }
        .test-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .test-duration {
            color: #666;
            font-size: 12px;
        }
        .error-list {
            margin-top: 10px;
            padding-left: 20px;
        }
        .error-item {
            color: #ff4d4f;
            font-family: monospace;
            font-size: 12px;
            margin: 2px 0;
        }
        .footer {
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #f0f0f0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Responsive Behavior Test Report</h1>
            <div class="status">Overall Status: ${overallStatus}</div>
            <div>Generated: ${new Date(report.timestamp).toLocaleString()}</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">${report.totalTests}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${report.passedTests}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${report.failedTests}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${report.totalDuration}ms</div>
                <div class="stat-label">Total Duration</div>
            </div>
        </div>
        
        <div class="requirements">
            <h2>Requirements Coverage</h2>
            
            <div class="requirement ${summary.layoutBehavior ? 'passed' : 'failed'}">
                <span class="requirement-icon">${summary.layoutBehavior ? '✅' : '❌'}</span>
                <div>
                    <strong>Layout behavior across different screen sizes and devices</strong>
                    <div style="font-size: 12px; color: #666;">Requirement 1.4</div>
                </div>
            </div>
            
            <div class="requirement ${summary.sidebarFunctionality ? 'passed' : 'failed'}">
                <span class="requirement-icon">${summary.sidebarFunctionality ? '✅' : '❌'}</span>
                <div>
                    <strong>Sidebar collapse/expand functionality works properly</strong>
                    <div style="font-size: 12px; color: #666;">Requirement 2.4</div>
                </div>
            </div>
            
            <div class="requirement ${summary.modalPositioning ? 'passed' : 'failed'}">
                <span class="requirement-icon">${summary.modalPositioning ? '✅' : '❌'}</span>
                <div>
                    <strong>Modal positioning adapts correctly to different viewport sizes</strong>
                    <div style="font-size: 12px; color: #666;">Requirement 3.4</div>
                </div>
            </div>
            
            <div class="requirement ${summary.touchInteractions ? 'passed' : 'failed'}">
                <span class="requirement-icon">${summary.touchInteractions ? '✅' : '❌'}</span>
                <div>
                    <strong>Touch interactions and mobile-specific behaviors</strong>
                    <div style="font-size: 12px; color: #666;">Requirements 1.4, 2.4, 3.4</div>
                </div>
            </div>
            
            <div class="requirement ${summary.viewportAdaptation ? 'passed' : 'failed'}">
                <span class="requirement-icon">${summary.viewportAdaptation ? '✅' : '❌'}</span>
                <div>
                    <strong>Viewport adaptation and breakpoint handling</strong>
                    <div style="font-size: 12px; color: #666;">Requirements 1.4, 2.4, 3.4</div>
                </div>
            </div>
        </div>
        
        <div class="test-results">
            <h2>Detailed Test Results</h2>
            ${report.results.map(result => `
                <div class="test-result ${result.passed ? 'passed' : 'failed'}">
                    <div class="test-name">${result.testFile}</div>
                    <div class="test-duration">Duration: ${result.duration}ms</div>
                    ${result.errors.length > 0 ? `
                        <div class="error-list">
                            ${result.errors.map(error => `<div class="error-item">• ${error}</div>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `).join('')}
        </div>
        
        <div class="footer">
            <p>This report covers comprehensive responsive behavior testing including layout adaptation, sidebar functionality, modal positioning, and touch interactions.</p>
            <p>Generated by COT Studio Frontend Test Suite</p>
        </div>
    </div>
</body>
</html>`;
}

/**
 * Main execution function
 */
async function main() {
  try {
    const report = await runAllResponsiveTests();
    
    // Generate and save HTML report
    const htmlReport = generateHtmlReport(report);
    const reportPath = join(process.cwd(), 'responsive-test-report.html');
    writeFileSync(reportPath, htmlReport);
    
    // Generate and save JSON report
    const jsonReportPath = join(process.cwd(), 'responsive-test-report.json');
    writeFileSync(jsonReportPath, JSON.stringify(report, null, 2));
    
    // Print summary
    console.log('\n📊 Test Summary:');
    console.log(`Total Tests: ${report.totalTests}`);
    console.log(`Passed: ${report.passedTests}`);
    console.log(`Failed: ${report.failedTests}`);
    console.log(`Duration: ${report.totalDuration}ms`);
    console.log(`\n📄 Reports generated:`);
    console.log(`HTML: ${reportPath}`);
    console.log(`JSON: ${jsonReportPath}`);
    
    // Print requirement coverage
    console.log('\n✅ Requirements Coverage:');
    console.log(`Layout Behavior (1.4): ${report.summary.layoutBehavior ? 'PASSED' : 'FAILED'}`);
    console.log(`Sidebar Functionality (2.4): ${report.summary.sidebarFunctionality ? 'PASSED' : 'FAILED'}`);
    console.log(`Modal Positioning (3.4): ${report.summary.modalPositioning ? 'PASSED' : 'FAILED'}`);
    console.log(`Touch Interactions: ${report.summary.touchInteractions ? 'PASSED' : 'FAILED'}`);
    console.log(`Viewport Adaptation: ${report.summary.viewportAdaptation ? 'PASSED' : 'FAILED'}`);
    
    // Exit with appropriate code
    process.exit(report.failedTests > 0 ? 1 : 0);
    
  } catch (error) {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

export { runAllResponsiveTests, generateHtmlReport };
export type { TestReport, TestResult };