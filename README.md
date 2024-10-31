# NutritionAgent 营养师食谱定制系统

> 一个基于 FastAPI 和 LLM 的智能营养师系统，可以根据用户的健康状况和饮食偏好，生成个性化的营养餐饮方案。

## 🌟 系统架构

A[FastAPI Web服务] --> B[分析模块/AnalysisModule]
A --> C[框架模块/FrameModule]
A --> D[评估模块/EvaluationModule]
B --> E[LLM服务]
C --> E
D --> E
C --> F[默认食谱库]

## 🚀 主要特性

- 支持异步处理大规模请求
- 基于用户画像的个性化推荐
- 批处理7天21餐食谱定制任务
- 分级错误重试机制及自定义兜底食材菜品库
- 食材替换
- 健康报告PDF分析
- 完整的错误处理和日志系统


## 🔄 主要流程

1. **食谱定制流程**:

   a. **用户分析阶段**
   - 分析用户基础信息（年龄、性别、身高体重等）
   - 解析健康目标和饮食禁忌
   - 确定营养需求和口味偏好

   b. **食材规划阶段**
   ```python
   # 生成7天21餐的食材规划
   ingredient_input = {
       "analysis_result": analysis_result,
       "user_info": user_info,
       "food_database": self.get_food_database()
   }
   ingredient_result = await self.async_call_llm(
       frame_prompt.ingredient_generation_prompt, 
       ingredient_input, 
       output_parser_type="json"
   )
   ```

   c. **批量制作阶段**
   - 并行处理7天21餐的食谱生成
   - 每个餐次独立生成，提高效率
   - 使用分级错误重试机制
   ```python
   batch_inputs = []
   for day in range(1, 8):
       for meal in ['早餐', '午餐', '晚餐']:
           batch_inputs.append({
               'batch_name': f"{day}_{meal}",
               'prompt_template': frame_prompt.meal_plan_prompt,
               'invoke_input': {
                   "analysis_result": analysis_result,
                   "user_info": user_info,
                   "meal_ingredients": recommended_ingredients[str(day)][meal],
                   "day": str(day),
                   "meal": meal
               }
           })
   ```

   d. **自动评估优化**
   - 评估每餐营养均衡性
   - 检查食材多样性
   - 验证与用户需求匹配度
   - 必要时进行菜品重新生成

   e. **兜底保障机制**
   - 默认食谱库作为备选方案
   - 确保服务高可用性
   ```python
   if not result:
       logging.warning(f"{batch_name} 生成失败，使用默认方案")
       weekly_meal_plan.append(self._get_default_meal_plan(day, meal))
   ```

2. **食材替换流程**:

   a. **替换请求处理**
   - 保留用户指定的菜品
   - 仅替换标记的菜品
   - 维持原有的customizedId

   b. **替换生成**
   ```python
   prompt_input = {
       "meal_type": input_data['mealTypeText'],
       "user_info": input_data['user_info'],
       "replace_foods": input_data['replaceFoodList'],
       "remain_foods": input_data['remainFoodList']
   }
   ```

   c. **默认替换机制**
   ```python
   if not llm_result:
       # 使用默认库生成替换方案
       default_meal = self._get_default_meal_plan(1, input_data['mealTypeText'])
       default_dishes = default_meal['menu']['dishes']
   ```

## 🎯 配置说明

### 环境变量配置 (.env)

1. **LLM服务配置**
```env
# Moonshot API配置
MOONSHOT_API_KEY=your_moonshot_api_key
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1

# DashScope API配置（包含备用密钥）
DASHSCOPE_API_KEY=your_primary_key
DASHSCOPE_API_KEY_BACKUP=your_backup_key

# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key

# 日志配置
LOG_PATH=app/app.log
```

### Docker部署配置

1. **测试环境 (nutrition-agent-test)**
```yaml
services:
  nutrition-agent-test:
    image: registry.cn-hangzhou.aliyuncs.com/big-head/nutrition-agent:latest
    container_name: nutrition-agent-test
    ports:
      - "8088:8000"
    volumes:
      - ./.env:/app/.env
    environment:
      - ENV=test
      - PDF_ANALYSIS_SUBMIT_URL=http://your-test-api/receivePdfResult
      - MEAL_PLAN_SUBMIT_URL=http://your-test-api/receiveFoodCustomizedResult
      - MEAL_PLAN_REPLACE_URL=http://your-test-api/receiveFoodCustomizedReplace
```

2. **开发环境 (nutrition-agent-dev)**
```yaml
services:
  nutrition-agent-dev:
    image: registry.cn-hangzhou.aliyuncs.com/big-head/nutrition-agent:latest
    container_name: nutrition-agent-dev
    ports:
      - "8000:8000"
    volumes:
      - ./.env:/app/.env
    environment:
      - ENV=dev
      - PDF_ANALYSIS_SUBMIT_URL=http://your-dev-api/receivePdfResult
      - MEAL_PLAN_SUBMIT_URL=http://your-dev-api/receiveFoodCustomizedResult
      - MEAL_PLAN_REPLACE_URL=http://your-dev-api/receiveFoodCustomizedReplace
```

### 配置说明

1. **环境变量**
   - `ENV`: 运行环境（dev/test）
   - `*_SUBMIT_URL`: 各功能模块的回调接口
   - `*_API_KEY`: LLM服务的访问密钥
   - `LOG_PATH`: 日志文件路径

2. **端口映射**
   - 测试环境: `8088:8000`
   - 开发环境: `8000:8000`

3. **数据卷挂载**
   - `.env` 文件挂载到容器内的 `/app/.env`

4. **注意事项**
   - 请确保在部署前正确配置所有环境变量
   - API密钥请妥善保管，不要提交到版本控制系统
   - 建议使用环境变量管理敏感信息
   - 不同环境使用不同的回调接口，避免交叉影响

## 🚀 项目启动

### 方式一：本地环境启动

1. **环境准备**
bash
创建虚拟环境
python -m venv venv
激活虚拟环境
Windows
venv\Scripts\activate
Linux/Mac
source venv/bin/activate
安装依赖
pip install -r requirements.txt
bash
复制环境变量模板
cp .env.example .env
修改.env文件，填入必要的配置
vim .env
bash
使用uvicorn启动
python app/main.py

### 方式二：Docker Compose启动

1. **开发环境**
bash
启动开发环境
docker-compose up nutrition-agent-dev
服务将在 http://localhost:8000 启动
2. **测试环境**
bash
启动测试环境
docker-compose up nutrition-agent-test
服务将在 http://localhost:8088 启动

### 环境要求

- Python 3.8+
- FastAPI
- uvicorn
- Docker & Docker Compose (如使用容器部署)

### 配置文件说明

1. **.env 文件**