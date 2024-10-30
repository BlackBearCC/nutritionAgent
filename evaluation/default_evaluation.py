class DefaultEvaluation:
    @staticmethod
    def get_default_evaluation(weekly_meal_plan=None, is_follow_up=False):
        """生成默认的评估结果"""
        basic_evaluation = {
            "overall_score": 85,
            "general_comments": "系统生成的默认评估：食谱整体符合健康饮食标准，建议适当调整以更好满足个性化需求。",
            "improvement_suggestions": [
                {
                    "day": 1,
                    "meal": "早餐",
                    "issue": "建议增加蛋白质",
                    "suggestion": "可以添加一个水煮蛋或豆浆"
                }
            ]
        }
        
        # 如果是跟进评估，添加evaluation_complete字段
        if is_follow_up:
            basic_evaluation["evaluation_complete"] = True
            
        return basic_evaluation