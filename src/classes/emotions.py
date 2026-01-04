from enum import Enum

class EmotionType(Enum):
    CALM = "平静"
    HAPPY = "开心"
    ANGRY = "愤怒"
    SAD = "悲伤"
    FEARFUL = "恐惧"
    SURPRISED = "惊讶"
    ANTICIPATING = "期待"
    DISGUSTED = "厌恶"
    CONFUSED = "疑惑"
    TIRED = "疲惫"

# 情绪对应的 Emoji 配置
EMOTION_EMOJIS = {
    EmotionType.CALM: "😌",
    EmotionType.HAPPY: "😄",
    EmotionType.ANGRY: "😡",
    EmotionType.SAD: "😢",
    EmotionType.FEARFUL: "😨",
    EmotionType.SURPRISED: "😲",
    EmotionType.ANTICIPATING: "🤩",
    EmotionType.DISGUSTED: "🤢",
    EmotionType.CONFUSED: "😕",
    EmotionType.TIRED: "😫",
}
