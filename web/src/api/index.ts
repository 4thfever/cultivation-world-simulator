// 导出子模块
export { worldApi } from './modules/world';
export { avatarApi, type HoverParams } from './modules/avatar';
export { systemApi } from './modules/system';
export { llmApi } from './modules/llm';
export { eventApi } from './modules/event';

// 保持向后兼容的聚合对象 (Optional, for transition)
// 但这次我们直接重构，不再保留大对象，鼓励按需引用
