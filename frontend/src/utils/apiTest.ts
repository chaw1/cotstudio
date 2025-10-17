/**
 * API测试工具 - 用于验证后端API端点的可用性
 */

import { apiClient } from './apiClient';

interface TestResult {
  endpoint: string;
  success: boolean;
  status?: number;
  error?: string;
  responseTime?: number;
  data?: any;
}

class ApiTester {
  private results: TestResult[] = [];

  async testEndpoint(endpoint: string, description: string): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      console.log(`Testing ${description}: ${endpoint}`);
      
      const response = await apiClient.get(endpoint);
      const responseTime = Date.now() - startTime;
      
      const result: TestResult = {
        endpoint,
        success: true,
        responseTime,
        data: response
      };
      
      console.log(`✅ ${description} - Success (${responseTime}ms)`);
      this.results.push(result);
      return result;
      
    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      
      const result: TestResult = {
        endpoint,
        success: false,
        status: error.status || 0,
        error: error.message || 'Unknown error',
        responseTime
      };
      
      console.error(`❌ ${description} - Failed (${responseTime}ms):`, error.message);
      this.results.push(result);
      return result;
    }
  }

  async runAllTests(): Promise<TestResult[]> {
    console.log('🚀 Starting API endpoint tests...\n');
    
    // 清空之前的结果
    this.results = [];
    
    // 测试系统监控相关端点
    await this.testEndpoint('/system/resources', 'System Resources API');
    await this.testEndpoint('/system/health', 'System Health API');
    await this.testEndpoint('/system/cpu', 'CPU Usage API');
    await this.testEndpoint('/system/memory', 'Memory Usage API');
    await this.testEndpoint('/system/disk', 'Disk Usage API');
    
    // 测试分析相关端点
    await this.testEndpoint('/analytics/user-contributions', 'User Contributions API');
    await this.testEndpoint('/analytics/dashboard-stats', 'Dashboard Stats API');
    await this.testEndpoint('/analytics/activity-timeline', 'Activity Timeline API');
    
    // 输出测试总结
    this.printSummary();
    
    return this.results;
  }

  private printSummary(): void {
    const totalTests = this.results.length;
    const successfulTests = this.results.filter(r => r.success).length;
    const failedTests = totalTests - successfulTests;
    
    console.log('\n📊 Test Summary:');
    console.log(`Total tests: ${totalTests}`);
    console.log(`Successful: ${successfulTests}`);
    console.log(`Failed: ${failedTests}`);
    console.log(`Success rate: ${((successfulTests / totalTests) * 100).toFixed(1)}%`);
    
    if (failedTests > 0) {
      console.log('\n❌ Failed tests:');
      this.results
        .filter(r => !r.success)
        .forEach(result => {
          console.log(`  - ${result.endpoint}: ${result.error} (Status: ${result.status})`);
        });
    }
    
    // 显示响应时间统计
    const responseTimes = this.results
      .filter(r => r.success && r.responseTime)
      .map(r => r.responseTime!);
    
    if (responseTimes.length > 0) {
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      const maxResponseTime = Math.max(...responseTimes);
      const minResponseTime = Math.min(...responseTimes);
      
      console.log('\n⏱️ Response Time Statistics:');
      console.log(`Average: ${avgResponseTime.toFixed(0)}ms`);
      console.log(`Min: ${minResponseTime}ms`);
      console.log(`Max: ${maxResponseTime}ms`);
    }
  }

  getResults(): TestResult[] {
    return this.results;
  }

  getFailedTests(): TestResult[] {
    return this.results.filter(r => !r.success);
  }

  getSuccessfulTests(): TestResult[] {
    return this.results.filter(r => r.success);
  }
}

// 导出单例实例
export const apiTester = new ApiTester();

// 便捷函数
export const testAllApis = () => apiTester.runAllTests();
export const testSingleApi = (endpoint: string, description: string) => 
  apiTester.testEndpoint(endpoint, description);